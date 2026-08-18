from __future__ import annotations

from ec2_manager.config.models import FeaturesConfig

START = "start"
STOP = "stop"
RESTART = "restart"

ENABLED_WHEN = {
    START: frozenset({"stopped"}),
    STOP: frozenset({"running"}),
    RESTART: frozenset({"running"}),
}

TRANSITIONAL_STATES = frozenset(
    {"pending", "stopping", "rebooting", "shutting-down", "terminated"}
)


def is_action_visible(action: str, features: FeaturesConfig) -> bool:
    mapping = {
        START: features.allow_start,
        STOP: features.allow_stop,
        RESTART: features.allow_restart,
    }
    return mapping.get(action, False)


def is_action_enabled(
    action: str,
    state: str,
    *,
    in_flight: bool = False,
    visible: bool = True,
) -> bool:
    if not visible or in_flight:
        return False
    return state in ENABLED_WHEN.get(action, frozenset())


def rdp_connect_enabled(
    state: str,
    *,
    rdp_enabled: bool,
    has_address: bool,
    readiness_ok: bool = True,
) -> bool:
    return bool(rdp_enabled and has_address and state == "running" and readiness_ok)
