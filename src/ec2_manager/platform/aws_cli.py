from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class AwsCliError(RuntimeError):
    """Raised when AWS CLI v2 is missing or SSO login fails."""


def find_aws_cli() -> Path | None:
    located = shutil.which("aws")
    if located:
        return Path(located)
    if shutil.which("aws.cmd"):
        found = shutil.which("aws.cmd")
        return Path(found) if found else None
    windows_guesses = (
        Path(r"C:\Program Files\Amazon\AWSCLIV2\aws.exe"),
        Path(r"C:\Program Files (x86)\Amazon\AWSCLIV2\aws.exe"),
    )
    for candidate in windows_guesses:
        if candidate.is_file():
            return candidate
    return None


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
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    output = f"{completed.stdout} {completed.stderr}"
    return "aws-cli/2" in output


def sso_login(profile_name: str, aws_path: Path | None = None) -> None:
    cli = aws_path or require_aws_cli()
    completed = subprocess.run(
        [str(cli), "sso", "login", "--profile", profile_name],
        check=False,
    )
    if completed.returncode != 0:
        raise AwsCliError(
            "AWS IAM Identity Center login did not complete. "
            "Sign in through the browser and try again."
        )
