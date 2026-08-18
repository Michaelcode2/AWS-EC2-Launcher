from __future__ import annotations

import tomllib
from pathlib import Path
from typing import cast

from ec2_manager.config.models import (
    ApplicationConfig,
    AwsConfig,
    CustomerProfile,
    FeaturesConfig,
    FilterMode,
    FiltersConfig,
    RdpConfig,
)
from ec2_manager.config.validation import (
    ConfigError,
    optional_bool,
    optional_int,
    reject_secrets,
    require_str,
)
from ec2_manager.platform.paths import bundled_config_dir, user_config_dir

_VALID_MODES: set[str] = {"all", "instance_ids", "tags"}


def load_profile(path: Path) -> CustomerProfile:
    try:
        raw = path.read_text(encoding="utf-8")
        data = tomllib.loads(raw)
    except OSError as exc:
        raise ConfigError(f"Could not read profile {path}: {exc}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML in {path}: {exc}") from exc

    reject_secrets(data)
    return _parse_profile(data, source_path=str(path))


def load_profiles(directories: list[Path] | None = None) -> list[CustomerProfile]:
    profiles: list[CustomerProfile] = []
    errors: list[str] = []
    for directory in directories or default_profile_directories():
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.toml")):
            try:
                profiles.append(load_profile(path))
            except ConfigError as exc:
                errors.append(str(exc))
    if not profiles and errors:
        raise ConfigError("No valid profiles found. " + " ".join(errors))
    return profiles


def default_profile_directories() -> list[Path]:
    return [user_config_dir(), bundled_config_dir()]


def _parse_profile(data: dict[str, object], *, source_path: str) -> CustomerProfile:
    application_raw = _section(data, "application")
    aws_raw = _section(data, "aws")
    expected_account_id = require_str(
        application_raw, "expected_account_id", section_name="application"
    )
    if not expected_account_id.isdigit() or len(expected_account_id) != 12:
        raise ConfigError("application.expected_account_id must be a 12-digit AWS account ID.")

    default_region = require_str(application_raw, "default_region", section_name="application")
    if not default_region:
        raise ConfigError("Select or configure an AWS region.")

    application = ApplicationConfig(
        name=require_str(application_raw, "name", section_name="application"),
        expected_account_id=expected_account_id,
        default_region=default_region,
        refresh_interval_seconds=optional_int(application_raw, "refresh_interval_seconds", 15),
        confirm_start=optional_bool(application_raw, "confirm_start", False),
    )
    aws = AwsConfig(profile=require_str(aws_raw, "profile", section_name="aws"))
    return CustomerProfile(
        source_path=source_path,
        application=application,
        aws=aws,
        filters=_parse_filters(data.get("filters")),
        rdp=_parse_rdp(data.get("rdp")),
        features=_parse_features(data.get("features")),
    )


def _section(data: dict[str, object], name: str) -> dict[str, object]:
    value = data.get(name)
    if not isinstance(value, dict):
        raise ConfigError(f"[{name}] section is required.")
    return value


def _parse_filters(raw: object) -> FiltersConfig:
    if raw is None:
        return FiltersConfig()
    if not isinstance(raw, dict):
        raise ConfigError("[filters] must be a table.")
    mode = str(raw.get("mode", "all"))
    if mode not in _VALID_MODES:
        raise ConfigError("filters.mode must be all, instance_ids, or tags.")
    instance_ids_raw = raw.get("instance_ids", [])
    if instance_ids_raw is None:
        instance_ids_raw = []
    if not isinstance(instance_ids_raw, list) or not all(
        isinstance(item, str) for item in instance_ids_raw
    ):
        raise ConfigError("filters.instance_ids must be a list of strings.")
    tags_raw = raw.get("tags", {})
    if tags_raw is None:
        tags_raw = {}
    if not isinstance(tags_raw, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in tags_raw.items()
    ):
        raise ConfigError("filters.tags must be a table of string values.")
    return FiltersConfig(
        mode=cast(FilterMode, mode),
        instance_ids=tuple(instance_ids_raw),
        tags=dict(tags_raw),
    )


def _parse_rdp(raw: object) -> RdpConfig:
    if raw is None:
        return RdpConfig()
    if not isinstance(raw, dict):
        raise ConfigError("[rdp] must be a table.")
    elastic_ip = raw.get("elastic_ip")
    if elastic_ip is not None and not isinstance(elastic_ip, str):
        raise ConfigError("rdp.elastic_ip must be a string.")
    elastic = elastic_ip.strip() if isinstance(elastic_ip, str) and elastic_ip.strip() else None
    return RdpConfig(
        enabled=optional_bool(raw, "enabled", True),
        use_elastic_ip=optional_bool(raw, "use_elastic_ip", True),
        check_readiness=optional_bool(raw, "check_readiness", False),
        elastic_ip=elastic,
    )


def _parse_features(raw: object) -> FeaturesConfig:
    if raw is None:
        return FeaturesConfig()
    if not isinstance(raw, dict):
        raise ConfigError("[features] must be a table.")
    return FeaturesConfig(
        allow_start=optional_bool(raw, "allow_start", True),
        allow_stop=optional_bool(raw, "allow_stop", True),
        allow_restart=optional_bool(raw, "allow_restart", True),
    )

