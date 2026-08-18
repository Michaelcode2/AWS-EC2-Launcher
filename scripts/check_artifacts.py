#!/usr/bin/env python3
"""Fail if build outputs or shipped files look like they contain secrets.

Identifier names such as aws_access_key_id appear in boto3/botocore, in Nuitka
compile intermediates, and in this app's own validation and log-redaction
code. Those are not credentials. This scanner looks for credential *values*
(AWS access key IDs and PEM private keys) everywhere, and for forbidden
config key names only in configuration files.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# AWS documentation placeholders, not real credentials.
# https://docs.aws.amazon.com/IAM/latest/UserGuide/access-keys-access-advisor.html
DOCUMENTED_EXAMPLE_ACCESS_KEYS = {
    b"AKIAIOSFODNN7EXAMPLE",
    b"AKIAI44QH8DHBEXAMPLE",
}

ACCESS_KEY_RE = re.compile(rb"AKIA[0-9A-Z]{16}", re.IGNORECASE)

PEM_MARKERS = (
    b"BEGIN PRIVATE KEY",
    b"BEGIN RSA PRIVATE KEY",
)

# Flag these only in config files, where they would mean a secret was stored.
CONFIG_KEY_NAMES = (
    b"aws_secret_access_key",
    b"aws_access_key_id",
    b"windows_password",
)

CONFIG_SUFFIXES = {".toml", ".env", ".ini", ".cfg", ".yaml", ".yml"}

SKIP_SUFFIXES = {".png", ".ico", ".exe", ".dll", ".pyd", ".so", ".zip", ".pyc", ".pyo"}
SKIP_DIR_NAMES = {"__pycache__"}


def _is_documented_example_key(key: bytes) -> bool:
    upper = key.upper()
    if upper in {item.upper() for item in DOCUMENTED_EXAMPLE_ACCESS_KEYS}:
        return True
    return upper.endswith(b"EXAMPLE")


def scan(root: Path) -> list[str]:
    hits: list[str] = []
    if not root.exists():
        return hits
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() in SKIP_SUFFIXES:
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.name == "check_artifacts.py":
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        hits.extend(_hits_for_file(path, data))
    return hits


def _hits_for_file(path: Path, data: bytes) -> list[str]:
    hits: list[str] = []
    for match in ACCESS_KEY_RE.finditer(data):
        key = match.group(0)
        if _is_documented_example_key(key):
            continue
        hits.append(f"{path}: contains AWS access key id")
        break
    for marker in PEM_MARKERS:
        if marker in data:
            hits.append(f"{path}: contains {marker.decode()}")
    if path.suffix.lower() in CONFIG_SUFFIXES:
        lowered = data.lower()
        for token in CONFIG_KEY_NAMES:
            if token in lowered:
                hits.append(f"{path}: contains {token.decode()}")
    return hits


def main() -> int:
    roots = [Path(arg) for arg in sys.argv[1:]] or [
        Path("config"),
        Path("scripts"),
        Path("dist"),
    ]
    hits: list[str] = []
    for root in roots:
        hits.extend(scan(root))
    if hits:
        print("Secret-like content found:")
        for hit in hits:
            print(f"  {hit}")
        return 1
    print("No secret-like content found in", ", ".join(str(r) for r in roots))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
