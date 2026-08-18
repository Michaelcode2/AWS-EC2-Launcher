from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ec2_manager.aws.actions import (
    ActionTimeoutError,
    reboot_instance,
    start_instance,
    stop_instance,
    wait_for_state,
)
from ec2_manager.aws.errors import AwsUserError, map_aws_error
from ec2_manager.aws.identity import CallerIdentity, get_caller_identity, verify_account
from ec2_manager.aws.inventory import Ec2Instance, list_instances
from ec2_manager.aws.session import create_session
from ec2_manager.config.models import CustomerProfile
from ec2_manager.filters import apply_filters
from ec2_manager.host.aws_cli import authenticate_profile
from ec2_manager.logging_config import get_logger
from ec2_manager.rdp.launcher import launch_rdp, rdp_ready, select_rdp_address
from ec2_manager.state_logic import rdp_connect_enabled

log = get_logger()


@dataclass
class AppSession:
    profile: CustomerProfile
    region: str
    identity: CallerIdentity
    session: Any
    inventory: list[Ec2Instance] = field(default_factory=list)
    in_flight: set[str] = field(default_factory=set)
    rdp_ready_hosts: dict[str, bool] = field(default_factory=dict)


def login(profile: CustomerProfile, *, region: str | None = None) -> AppSession:
    selected_region = region or profile.application.default_region
    if not selected_region:
        raise AwsUserError("Select or configure an AWS region.")
    _audit("login_started", profile=profile, region=selected_region)
    authenticate_profile(profile.aws.profile)
    session = create_session(profile_name=profile.aws.profile, region_name=selected_region)
    identity = verify_account(
        get_caller_identity(session.client("sts")),
        profile.application.expected_account_id,
    )
    _audit(
        "login_succeeded",
        profile=profile,
        region=selected_region,
        account=identity.account,
        principal=identity.arn,
    )
    app = AppSession(
        profile=profile,
        region=selected_region,
        identity=identity,
        session=session,
    )
    refresh_inventory(app)
    return app


def logout(app: AppSession | None) -> None:
    if app is None:
        return
    _audit("logout", profile=app.profile, region=app.region, account=app.identity.account)
    app.inventory.clear()
    app.in_flight.clear()
    app.session = None


def refresh_inventory(app: AppSession) -> list[Ec2Instance]:
    try:
        discovered = list_instances(app.session.client("ec2"))
        app.inventory = apply_filters(discovered, app.profile.filters)
        _audit(
            "refresh",
            profile=app.profile,
            region=app.region,
            account=app.identity.account,
            result="ok",
        )
        return app.inventory
    except Exception as exc:
        mapped = map_aws_error(exc)
        _audit(
            "refresh",
            profile=app.profile,
            region=app.region,
            account=app.identity.account,
            result="error",
            error_code=type(mapped).__name__,
        )
        raise mapped from exc


def start_selected(app: AppSession, instance_id: str, *, sleep: Any) -> None:
    _run_action(
        app,
        instance_id,
        action_name="Start",
        expected="running",
        call=start_instance,
        sleep=sleep,
    )


def stop_selected(app: AppSession, instance_id: str, *, sleep: Any) -> None:
    _run_action(
        app,
        instance_id,
        action_name="Stop",
        expected="stopped",
        call=stop_instance,
        sleep=sleep,
    )


def restart_selected(app: AppSession, instance_id: str, *, sleep: Any) -> None:
    _run_action(
        app,
        instance_id,
        action_name="Restart",
        expected="running",
        call=reboot_instance,
        sleep=sleep,
    )


def connect_rdp(app: AppSession, instance: Ec2Instance) -> str:
    address = select_rdp_address(instance, app.profile.rdp)
    if not address:
        raise AwsUserError("No RDP address is available for this instance.")
    if app.profile.rdp.check_readiness and not rdp_ready(address):
        app.rdp_ready_hosts[instance.instance_id] = False
        raise AwsUserError("EC2 is running, but Windows/RDP is not ready yet.")
    launch_rdp(address)
    _audit(
        "rdp_connect",
        profile=app.profile,
        region=app.region,
        account=app.identity.account,
        instance_id=instance.instance_id,
        result="ok",
    )
    return address


def instance_rdp_enabled(app: AppSession, instance: Ec2Instance) -> bool:
    address = select_rdp_address(instance, app.profile.rdp)
    ready = True
    if app.profile.rdp.check_readiness:
        ready = app.rdp_ready_hosts.get(instance.instance_id, False)
        if (
            address
            and instance.state == "running"
            and instance.instance_id not in app.rdp_ready_hosts
        ):
            ready = rdp_ready(address)
            app.rdp_ready_hosts[instance.instance_id] = ready
    return rdp_connect_enabled(
        instance.state,
        rdp_enabled=app.profile.rdp.enabled,
        has_address=bool(address),
        readiness_ok=ready,
    )


def _run_action(
    app: AppSession,
    instance_id: str,
    *,
    action_name: str,
    expected: str,
    call: Any,
    sleep: Any,
) -> None:
    inventory_ids = {item.instance_id for item in app.inventory}
    app.in_flight.add(instance_id)
    try:
        _audit(
            action_name.lower(),
            profile=app.profile,
            region=app.region,
            account=app.identity.account,
            instance_id=instance_id,
            principal=app.identity.arn,
        )
        call(app.session.client("ec2"), instance_id, inventory_ids)
        wait_for_state(app.session.client("ec2"), instance_id, expected, sleep=sleep)
        refresh_inventory(app)
        _audit(
            action_name.lower(),
            profile=app.profile,
            region=app.region,
            account=app.identity.account,
            instance_id=instance_id,
            result="ok",
        )
    except ActionTimeoutError as exc:
        _audit(
            action_name.lower(),
            profile=app.profile,
            region=app.region,
            account=app.identity.account,
            instance_id=instance_id,
            result="timeout",
        )
        raise AwsUserError(str(exc)) from exc
    except Exception as exc:
        mapped = map_aws_error(exc, action=action_name)
        _audit(
            action_name.lower(),
            profile=app.profile,
            region=app.region,
            account=app.identity.account,
            instance_id=instance_id,
            result="error",
            error_code=type(mapped).__name__,
        )
        raise mapped from exc
    finally:
        app.in_flight.discard(instance_id)


def _audit(
    action: str,
    *,
    profile: CustomerProfile,
    region: str,
    account: str | None = None,
    instance_id: str | None = None,
    result: str | None = None,
    error_code: str | None = None,
    principal: str | None = None,
) -> None:
    parts = [
        f"action={action}",
        f"profile={profile.application.name}",
        f"region={region}",
        f"timestamp={datetime.now(UTC).isoformat()}",
    ]
    if account:
        parts.append(f"account={account}")
    if instance_id:
        parts.append(f"instance_id={instance_id}")
    if result:
        parts.append(f"result={result}")
    if error_code:
        parts.append(f"error_code={error_code}")
    if principal:
        parts.append(f"principal={principal}")
    log.info(" ".join(parts))
