from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from ec2_manager.platform.aws_cli import AwsCliError, _prefer_exe, sso_login


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
    assert command == ["C:/aws/aws.exe", "sso", "login", "--profile", "customer-server"]


def test_sso_login_nonzero_exit() -> None:
    runner = Mock(return_value=Mock(returncode=1))
    with pytest.raises(AwsCliError, match="did not complete"):
        sso_login("p", aws_path=Path("aws"), profiles={"p"}, runner=runner)


def test_prefer_exe_over_cmd(tmp_path: Path) -> None:
    exe = tmp_path / "aws.exe"
    cmd = tmp_path / "aws.cmd"
    exe.write_text("", encoding="utf-8")
    cmd.write_text("", encoding="utf-8")
    assert _prefer_exe(cmd) == exe
