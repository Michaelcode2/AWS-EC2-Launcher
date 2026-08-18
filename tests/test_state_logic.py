from __future__ import annotations

from ec2_manager.config.models import FeaturesConfig
from ec2_manager.state_logic import (
    RESTART,
    START,
    STOP,
    is_action_enabled,
    is_action_visible,
    rdp_connect_enabled,
)

DISABLED_STATES = ("pending", "stopping", "rebooting", "shutting-down", "terminated")


def test_stopped_enables_start_only() -> None:
    assert is_action_enabled(START, "stopped") is True
    assert is_action_enabled(STOP, "stopped") is False
    assert is_action_enabled(RESTART, "stopped") is False


def test_running_enables_stop_and_restart() -> None:
    assert is_action_enabled(START, "running") is False
    assert is_action_enabled(STOP, "running") is True
    assert is_action_enabled(RESTART, "running") is True


def test_transitional_states_disable_all() -> None:
    for state in DISABLED_STATES:
        assert is_action_enabled(START, state) is False
        assert is_action_enabled(STOP, state) is False
        assert is_action_enabled(RESTART, state) is False


def test_in_flight_disables_actions() -> None:
    assert is_action_enabled(START, "stopped", in_flight=True) is False
    assert is_action_enabled(STOP, "running", in_flight=True) is False


def test_feature_flags_hide_actions() -> None:
    hidden = FeaturesConfig(allow_start=True, allow_stop=False, allow_restart=False)
    assert is_action_visible(START, hidden) is True
    assert is_action_visible(STOP, hidden) is False
    assert is_action_visible(RESTART, hidden) is False
    assert is_action_enabled(STOP, "running", visible=False) is False


def test_rdp_disabled_until_running() -> None:
    assert rdp_connect_enabled("pending", rdp_enabled=True, has_address=True) is False
    assert rdp_connect_enabled("running", rdp_enabled=True, has_address=True) is True
    assert rdp_connect_enabled(
        "running", rdp_enabled=True, has_address=True, readiness_ok=False
    ) is False
