from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

StateFamily = Literal["running", "stopped", "transitional", "terminated", "unknown"]

TRANSITIONAL_STATES = frozenset({"pending", "stopping", "rebooting", "shutting-down"})


@dataclass(frozen=True)
class StateStyle:
    family: StateFamily
    foreground: str
    background: str


def instance_state_style(state: str) -> StateStyle:
    normalized = state.strip().lower()
    if normalized == "running":
        return StateStyle("running", "#14532d", "#dcfce7")
    if normalized == "stopped":
        return StateStyle("stopped", "#7f1d1d", "#fee2e2")
    if normalized in TRANSITIONAL_STATES:
        return StateStyle("transitional", "#78350f", "#fef3c7")
    if normalized == "terminated":
        return StateStyle("terminated", "#374151", "#f3f4f6")
    return StateStyle("unknown", "#374151", "#f9fafb")


def shorten_iam_arn(arn: str) -> str:
    trimmed = arn.strip()
    if not trimmed:
        return trimmed
    parts = trimmed.split(":", 5)
    if len(parts) == 6 and parts[5]:
        return parts[5]
    if len(parts) >= 2 and parts[-1]:
        return parts[-1]
    return trimmed
