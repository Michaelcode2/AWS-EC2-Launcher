from __future__ import annotations

import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

from ec2_manager.host.paths import log_file_path
from ec2_manager.version import __version__

LOGGER_NAME = "ec2_manager"

_SECRET_PATTERNS = (
    re.compile(r"(?i)(aws_secret_access_key|secret_access_key|secret[_-]?key)\s*[=:]\s*\S+"),
    re.compile(r"(?i)(aws_session_token|session_token)\s*[=:]\s*\S+"),
    re.compile(r"(?i)(password|passwd|pwd)\s*[=:]\s*\S+"),
    re.compile(r"(?i)(refresh_token|private_key)\s*[=:]\s*\S+"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)aws_access_key_id\s*[=:]\s*\S+"),
)

_REDACTED = "[REDACTED]"


def redact_text(value: str) -> str:
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(_REDACTED, redacted)
    return redacted


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_text(str(record.msg))
        if record.args:
            if isinstance(record.args, dict):
                record.args = {key: _redact_arg(val) for key, val in record.args.items()}
            else:
                record.args = tuple(_redact_arg(arg) for arg in record.args)
        return True


def _redact_arg(value: object) -> object:
    if isinstance(value, str):
        return redact_text(value)
    return value


def configure_logging(log_file: Path | None = None) -> Path:
    path = log_file or log_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    redactor = RedactingFilter()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s version=%(app_version)s %(message)s"
    )

    file_handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.addFilter(redactor)
    logger.addHandler(file_handler)

    logger.addFilter(_VersionFilter())
    logger.info("logging_initialized path=%s", path)
    return path


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)


class _VersionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.app_version = __version__
        return True
