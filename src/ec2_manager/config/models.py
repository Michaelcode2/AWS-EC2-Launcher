from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

FilterMode = Literal["all", "instance_ids", "tags"]


@dataclass(frozen=True)
class ApplicationConfig:
    name: str
    expected_account_id: str
    default_region: str
    refresh_interval_seconds: int = 15
    confirm_start: bool = False


@dataclass(frozen=True)
class AwsConfig:
    profile: str


@dataclass(frozen=True)
class FiltersConfig:
    mode: FilterMode = "all"
    instance_ids: tuple[str, ...] = ()
    tags: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RdpConfig:
    enabled: bool = True
    use_elastic_ip: bool = True
    check_readiness: bool = False
    elastic_ip: str | None = None


@dataclass(frozen=True)
class FeaturesConfig:
    allow_start: bool = True
    allow_stop: bool = True
    allow_restart: bool = True


@dataclass(frozen=True)
class CustomerProfile:
    source_path: str
    application: ApplicationConfig
    aws: AwsConfig
    filters: FiltersConfig
    rdp: RdpConfig = field(default_factory=RdpConfig)
    features: FeaturesConfig = field(default_factory=FeaturesConfig)
