from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

IdleDecision = Literal["update_timestamp", "noop", "stop", "fail_safe"]


def decide_idle_action(
    *,
    active_sessions: int | None,
    last_active: datetime | None,
    now: datetime,
    idle_after: timedelta,
    aws_reachable: bool = True,
) -> IdleDecision:
    """Canonical idle algorithm for the on-instance Scheduled Task.

    Fail-safe: unknown session status or unreachable AWS leaves the instance running.
    """
    if not aws_reachable:
        return "fail_safe"
    if active_sessions is None:
        return "fail_safe"
    if active_sessions > 0:
        return "update_timestamp"
    if last_active is None:
        return "update_timestamp"
    if now - last_active < idle_after:
        return "noop"
    return "stop"
