from __future__ import annotations

from ec2_manager.gui.presentation import instance_state_style, shorten_iam_arn

USER_ARN = "arn:aws:iam::703096464034:user/EC2-App-Launcher"
ROLE_ARN = "arn:aws:iam::703096464034:role/EC2-Operator"


def test_running_state_style() -> None:
    style = instance_state_style("running")
    assert style.family == "running"
    assert style.foreground.startswith("#")
    assert style.background.startswith("#")


def test_stopped_state_style() -> None:
    style = instance_state_style("stopped")
    assert style.family == "stopped"


def test_transitional_state_styles() -> None:
    for state in ("pending", "stopping", "rebooting", "shutting-down"):
        assert instance_state_style(state).family == "transitional"


def test_terminated_state_style() -> None:
    assert instance_state_style("terminated").family == "terminated"


def test_unknown_state_style() -> None:
    assert instance_state_style("").family == "unknown"
    assert instance_state_style("custom-state").family == "unknown"


def test_shorten_user_arn() -> None:
    assert shorten_iam_arn(USER_ARN) == "user/EC2-App-Launcher"


def test_shorten_role_arn() -> None:
    assert shorten_iam_arn(ROLE_ARN) == "role/EC2-Operator"


def test_shorten_arn_preserves_full_value_for_tooltips() -> None:
    shortened = shorten_iam_arn(USER_ARN)
    assert shortened != USER_ARN
    assert USER_ARN.endswith(shortened.split("/", 1)[-1])
