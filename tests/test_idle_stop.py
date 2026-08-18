from __future__ import annotations

import importlib.util
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDLE_DIR = ROOT / "scripts" / "idle-stop"
DECISION_PATH = IDLE_DIR / "idle_decision.py"


def _load_decision():
    spec = importlib.util.spec_from_file_location("idle_decision", DECISION_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.decide_idle_action


decide_idle_action = _load_decision()


def test_active_session_updates_timestamp() -> None:
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    decision = decide_idle_action(
        active_sessions=2,
        last_active=now - timedelta(minutes=90),
        now=now,
        idle_after=timedelta(minutes=60),
    )
    assert decision == "update_timestamp"


def test_idle_timeout_stops() -> None:
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    decision = decide_idle_action(
        active_sessions=0,
        last_active=now - timedelta(minutes=60),
        now=now,
        idle_after=timedelta(minutes=60),
    )
    assert decision == "stop"


def test_unknown_session_fail_safe() -> None:
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    decision = decide_idle_action(
        active_sessions=None,
        last_active=now - timedelta(minutes=90),
        now=now,
        idle_after=timedelta(minutes=60),
    )
    assert decision == "fail_safe"


def test_aws_failure_fail_safe() -> None:
    assert (
        decide_idle_action(
            active_sessions=0,
            last_active=None,
            now=datetime.now(UTC),
            idle_after=timedelta(minutes=60),
            aws_reachable=False,
        )
        == "fail_safe"
    )


def test_scripts_contain_no_access_keys() -> None:
    forbidden = ("AKIA", "aws_secret_access_key", "aws_access_key_id", "SecretAccessKey")
    for path in IDLE_DIR.rglob("*"):
        if path.suffix.lower() in {".ps1", ".xml", ".json", ".md", ".py"}:
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                assert token not in text, path
