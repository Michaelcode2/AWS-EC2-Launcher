from __future__ import annotations

from pathlib import Path

from ec2_manager.logging_config import configure_logging, get_logger, redact_text


def test_redacts_keys_and_passwords() -> None:
    text = (
        "aws_secret_access_key = hunter2 "
        "aws_session_token=abc "
        "password=secret "
        "AKIAIOSFODNN7EXAMPLE"
    )
    redacted = redact_text(text)
    assert "hunter2" not in redacted
    assert "abc" not in redacted
    assert "secret" not in redacted
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted
    assert "[REDACTED]" in redacted


def test_log_file_redacts_and_uses_fallback_path(tmp_path: Path) -> None:
    log_file = tmp_path / "logs" / "app.log"
    configure_logging(log_file)
    logger = get_logger()
    logger.info("aws_secret_access_key = super-secret-value")
    for handler in logger.handlers:
        handler.flush()
    content = log_file.read_text(encoding="utf-8")
    assert "super-secret-value" not in content
    assert "version=" in content
