#!/usr/bin/env python3
"""Fail if build outputs or shipped files look like they contain secrets."""

from __future__ import annotations

import sys
from pathlib import Path

FORBIDDEN = (
    b"AKIA",
    b"aws_secret_access_key",
    b"aws_access_key_id",
    b"BEGIN PRIVATE KEY",
    b"BEGIN RSA PRIVATE KEY",
    b"windows_password",
)

SKIP_SUFFIXES = {".png", ".ico", ".exe", ".dll", ".pyd", ".so", ".zip"}


def scan(root: Path) -> list[str]:
    hits: list[str] = []
    if not root.exists():
        return hits
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() in SKIP_SUFFIXES:
            continue
        if path.name == "check_artifacts.py":
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        for token in FORBIDDEN:
            if token.lower() in data.lower():
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
