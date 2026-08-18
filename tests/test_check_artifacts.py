from __future__ import annotations

import sys
from pathlib import Path

import pytest

import scripts.check_artifacts as check_artifacts


def test_ignores_sdk_field_names_in_nuitka_intermediates(tmp_path: Path) -> None:
    build_dir = tmp_path / "dist" / "nuitka" / "main.build"
    build_dir.mkdir(parents=True)
    (build_dir / "module.boto3.session.c").write_text(
        "char *k = \"aws_secret_access_key\"; char *i = \"aws_access_key_id\";",
        encoding="utf-8",
    )
    (build_dir / "module.ec2_manager.config.validation.const").write_bytes(
        b"windows_password\naws_secret_access_key\naws_access_key_id\n"
    )
    (build_dir / "module.ec2_manager.logging_config.const").write_bytes(
        rb"AKIA[0-9A-Z]{16}"
    )
    assert check_artifacts.scan(tmp_path / "dist") == []


def test_allows_aws_documentation_example_keys(tmp_path: Path) -> None:
    examples = (
        tmp_path
        / "dist"
        / "nuitka"
        / "main.dist"
        / "botocore"
        / "data"
        / "iam"
        / "2010-05-08"
    )
    examples.mkdir(parents=True)
    (examples / "examples-1.json").write_text(
        '{"AccessKeyId": "AKIAIOSFODNN7EXAMPLE"}',
        encoding="utf-8",
    )
    assert check_artifacts.scan(tmp_path / "dist") == []


def test_flags_real_access_key_id(tmp_path: Path) -> None:
    path = tmp_path / "leaked.txt"
    path.write_text("id=AKIA0123456789ABCDEF", encoding="utf-8")
    hits = check_artifacts.scan(tmp_path)
    assert hits == [f"{path}: contains AWS access key id"]


def test_flags_forbidden_keys_in_config(tmp_path: Path) -> None:
    path = tmp_path / "profile.toml"
    path.write_text("windows_password = \"nope\"\n", encoding="utf-8")
    hits = check_artifacts.scan(tmp_path)
    assert f"{path}: contains windows_password" in hits


def test_flags_pem_private_key(tmp_path: Path) -> None:
    path = tmp_path / "key.pem"
    path.write_text("-----BEGIN PRIVATE KEY-----\nMIIB\n", encoding="utf-8")
    hits = check_artifacts.scan(tmp_path)
    assert hits == [f"{path}: contains BEGIN PRIVATE KEY"]


def test_skips_bytecode_cache(tmp_path: Path) -> None:
    cache = tmp_path / "scripts" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "check_artifacts.cpython-312.pyc").write_bytes(b"BEGIN PRIVATE KEY")
    assert check_artifacts.scan(tmp_path / "scripts") == []


def test_cli_passes_clean_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "ok.txt").write_text("no secrets here", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["check_artifacts.py", str(tmp_path)])
    assert check_artifacts.main() == 0
