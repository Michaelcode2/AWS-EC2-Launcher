from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from ec2_manager.aws.errors import InstanceNotInInventoryError, map_aws_error
from ec2_manager.aws.inventory import list_instances

FIRST_POLL_SECONDS = 5
POLL_INTERVAL_SECONDS = 15
MAX_WAIT_SECONDS = 10 * 60

Sleeper = Callable[[float], None]
Clock = Callable[[], datetime]


class ActionTimeoutError(Exception):
    def __init__(self, instance_id: str, expected_state: str) -> None:
        super().__init__(
            f"Timed out waiting for {instance_id} to become {expected_state}. Refresh manually."
        )
        self.instance_id = instance_id
        self.expected_state = expected_state


def assert_in_inventory(instance_id: str, inventory_ids: set[str]) -> None:
    if instance_id not in inventory_ids:
        raise InstanceNotInInventoryError(instance_id)


def start_instance(ec2_client: Any, instance_id: str, inventory_ids: set[str]) -> None:
    assert_in_inventory(instance_id, inventory_ids)
    _call(ec2_client.start_instances, instance_id, action="Start")


def stop_instance(ec2_client: Any, instance_id: str, inventory_ids: set[str]) -> None:
    assert_in_inventory(instance_id, inventory_ids)
    _call(ec2_client.stop_instances, instance_id, action="Stop")


def reboot_instance(ec2_client: Any, instance_id: str, inventory_ids: set[str]) -> None:
    assert_in_inventory(instance_id, inventory_ids)
    _call(ec2_client.reboot_instances, instance_id, action="Restart")


def wait_for_state(
    ec2_client: Any,
    instance_id: str,
    expected_state: str,
    *,
    sleep: Sleeper,
    clock: Clock | None = None,
    first_wait: float = FIRST_POLL_SECONDS,
    interval: float = POLL_INTERVAL_SECONDS,
    max_wait: float = MAX_WAIT_SECONDS,
) -> str:
    now = clock or (lambda: datetime.now(UTC))
    deadline = now() + timedelta(seconds=max_wait)
    sleep(first_wait)
    while now() <= deadline:
        instances = list_instances(ec2_client, now=now())
        match = next((item for item in instances if item.instance_id == instance_id), None)
        if match is None:
            raise InstanceNotInInventoryError(instance_id)
        if match.state == expected_state:
            return match.state
        remaining = (deadline - now()).total_seconds()
        if remaining <= 0:
            break
        sleep(min(interval, remaining))
    raise ActionTimeoutError(instance_id, expected_state)


def _call(method: Callable[..., Any], instance_id: str, *, action: str) -> None:
    try:
        method(InstanceIds=[instance_id])
    except Exception as exc:
        raise map_aws_error(exc, action=action) from exc
