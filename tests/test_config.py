from __future__ import annotations

from pathlib import Path

import pytest
from tests.helpers import EXAMPLE_PROFILE

from ec2_manager.config.loader import load_profile
from ec2_manager.config.validation import FORBIDDEN_KEYS, ConfigError


def test_example_profile_loads() -> None:
    profile = load_profile(EXAMPLE_PROFILE)
    assert profile.application.expected_account_id == "123456789012"
    assert profile.application.default_region == "eu-central-1"
    assert profile.aws.profile == "customer-server"
    assert profile.filters.mode == "tags"
    assert profile.filters.tags["ManagedBy"] == "ec2-desktop-manager"
    assert profile.features.allow_start is True


def test_example_profile_is_secret_free() -> None:
    text = EXAMPLE_PROFILE.read_text(encoding="utf-8").lower()
    for key in FORBIDDEN_KEYS:
        assert key not in text


def test_missing_region(tmp_path: Path) -> None:
    path = tmp_path / "bad.toml"
    path.write_text(
        """
[application]
name = "x"
expected_account_id = "123456789012"
default_region = ""

[aws]
profile = "p"
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="default_region"):
        load_profile(path)


def test_missing_account_id(tmp_path: Path) -> None:
    path = tmp_path / "bad.toml"
    path.write_text(
        """
[application]
name = "x"
default_region = "eu-central-1"

[aws]
profile = "p"
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="expected_account_id"):
        load_profile(path)


def test_invalid_toml(tmp_path: Path) -> None:
    path = tmp_path / "bad.toml"
    path.write_text("this is not = toml [", encoding="utf-8")
    with pytest.raises(ConfigError, match="Invalid TOML"):
        load_profile(path)


def test_rejects_secret_keys(tmp_path: Path) -> None:
    path = tmp_path / "secret.toml"
    path.write_text(
        """
[application]
name = "x"
expected_account_id = "123456789012"
default_region = "eu-central-1"

[aws]
profile = "p"
aws_secret_access_key = "should-not-be-here"
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="forbidden secret"):
        load_profile(path)
