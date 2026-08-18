from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from ec2_manager.host.aws_cli import (
    AwsCliError,
    _prefer_exe,
    authenticate_profile,
    profile_uses_sso,
    sso_login,
)


def test_sso_login_rejects_missing_profile() -> None:
    with pytest.raises(AwsCliError, match="was not found"):
        sso_login("customer-server", aws_path=Path("aws"), profiles=set())


def test_sso_login_runs_cli_when_profile_exists() -> None:
    runner = Mock(return_value=Mock(returncode=0))
    sso_login(
        "customer-server",
        aws_path=Path("C:/aws/aws.exe"),
        profiles={"customer-server"},
        runner=runner,
    )
    command = runner.call_args.args[0]
    assert command == [str(Path("C:/aws/aws.exe")), "sso", "login", "--profile", "customer-server"]


def test_sso_login_nonzero_exit() -> None:
    runner = Mock(return_value=Mock(returncode=1))
    with pytest.raises(AwsCliError, match="did not complete"):
        sso_login("p", aws_path=Path("aws"), profiles={"p"}, runner=runner)


def test_profile_uses_sso_detects_identity_center() -> None:
    assert profile_uses_sso("p", config={"sso_start_url": "https://example.awsapps.com/start"})
    assert profile_uses_sso("p", config={"sso_session": "my-sso"})
    assert not profile_uses_sso("p", config={"region": "eu-central-1"})


def test_authenticate_iam_profile_skips_sso_login() -> None:
    runner = Mock(return_value=Mock(returncode=0))
    authenticate_profile(
        "customer-server",
        aws_path=Path("C:/aws/aws.exe"),
        profiles={"customer-server"},
        config={"region": "eu-central-1"},
        runner=runner,
    )
    runner.assert_not_called()


def test_authenticate_sso_profile_runs_login() -> None:
    runner = Mock(return_value=Mock(returncode=0))
    authenticate_profile(
        "customer-server",
        aws_path=Path("C:/aws/aws.exe"),
        profiles={"customer-server"},
        config={"sso_start_url": "https://example.awsapps.com/start"},
        runner=runner,
    )
    command = runner.call_args.args[0]
    assert command == [str(Path("C:/aws/aws.exe")), "sso", "login", "--profile", "customer-server"]


def test_authenticate_rejects_missing_profile() -> None:
    with pytest.raises(AwsCliError, match="aws configure --profile"):
        authenticate_profile("missing", profiles=set(), config={})


def test_prefer_exe_over_cmd(tmp_path: Path) -> None:
    exe = tmp_path / "aws.exe"
    cmd = tmp_path / "aws.cmd"
    exe.write_text("", encoding="utf-8")
    cmd.write_text("", encoding="utf-8")
    assert _prefer_exe(cmd) == exe
