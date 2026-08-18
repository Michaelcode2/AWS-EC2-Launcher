from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

Runner = Callable[..., subprocess.CompletedProcess[str]]


class AwsCliError(RuntimeError):
    """Raised when AWS CLI v2 is missing or SSO login fails."""


def find_aws_cli() -> Path | None:
    located = shutil.which("aws")
    if located:
        return _prefer_exe(Path(located))
    cmd = shutil.which("aws.cmd")
    if cmd:
        return _prefer_exe(Path(cmd))
    windows_guesses = (
        Path(r"C:\Program Files\Amazon\AWSCLIV2\aws.exe"),
        Path(r"C:\Program Files (x86)\Amazon\AWSCLIV2\aws.exe"),
    )
    for candidate in windows_guesses:
        if candidate.is_file():
            return candidate
    return None


def _prefer_exe(path: Path) -> Path:
    if path.suffix.lower() == ".cmd":
        exe = path.with_name("aws.exe")
        if exe.is_file():
            return exe
    return path


def require_aws_cli() -> Path:
    path = find_aws_cli()
    if path is None:
        raise AwsCliError(
            "AWS CLI v2 was not found. Install AWS CLI v2 to sign in with IAM Identity Center."
        )
    return path


def is_aws_cli_v2(aws_path: Path | None = None) -> bool:
    path = aws_path or find_aws_cli()
    if path is None:
        return False
    try:
        completed = subprocess.run(
            [str(path), "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=_no_window_flags(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    output = f"{completed.stdout} {completed.stderr}"
    return "aws-cli/2" in output


def list_aws_profiles() -> frozenset[str]:
    from botocore.session import Session

    return frozenset(Session().available_profiles)


def sso_login(
    profile_name: str,
    aws_path: Path | None = None,
    *,
    runner: Runner | None = None,
    profiles: Iterable[str] | None = None,
) -> None:
    available = set(list_aws_profiles() if profiles is None else profiles)
    if profile_name not in available:
        raise AwsCliError(
            f'The AWS CLI profile "{profile_name}" was not found. '
            "Create an IAM Identity Center profile first, for example: aws configure sso"
        )
    cli = aws_path or require_aws_cli()
    execute = runner or subprocess.run
    command = [str(cli), "sso", "login", "--profile", profile_name]
    try:
        completed = execute(
            command,
            check=False,
            env=_login_env(),
            creationflags=_sso_console_flags(),
        )
    except OSError as exc:
        raise AwsCliError(f"Could not start AWS CLI: {exc}") from exc
    if completed.returncode != 0:
        raise AwsCliError(
            "AWS IAM Identity Center login did not complete. "
            "Finish sign-in in the browser (or the AWS CLI window) and try again."
        )


def _login_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("AWS_PAGER", "")
    env.setdefault("AWS_CLI_AUTO_PROMPT", "off")
    return env


def _sso_console_flags() -> int:
    """Give AWS CLI a real console on Windows so it can open the default browser."""
    if sys.platform != "win32" or not _parent_has_no_console():
        return 0
    return int(getattr(subprocess, "CREATE_NEW_CONSOLE", 0))


def _parent_has_no_console() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        windll = getattr(ctypes, "windll", None)
        if windll is None:
            return True
        get_console = getattr(windll.kernel32, "GetConsoleWindow", None)
        if get_console is None:
            return True
        return bool(get_console() == 0)
    except (AttributeError, OSError):
        return True


def _no_window_flags() -> int:
    if sys.platform != "win32":
        return 0
    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
