from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from ec2_manager.aws.inventory import Ec2Instance
from ec2_manager.config.models import (
    ApplicationConfig,
    AwsConfig,
    CustomerProfile,
    FeaturesConfig,
    FiltersConfig,
    RdpConfig,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PROFILE = ROOT / "config" / "example-profile.toml"


def make_profile(**overrides: object) -> CustomerProfile:
    profile = CustomerProfile(
        source_path="memory",
        application=ApplicationConfig(
            name="Example Customer",
            expected_account_id="123456789012",
            default_region="eu-central-1",
        ),
        aws=AwsConfig(profile="customer-server"),
        filters=FiltersConfig(mode="all"),
        rdp=RdpConfig(),
        features=FeaturesConfig(),
    )
    for key, value in overrides.items():
        object.__setattr__(profile, key, value)
    return profile


def make_instance(**overrides: object) -> Ec2Instance:
    data = {
        "instance_id": "i-0123456789abcdef0",
        "name": "app-server",
        "state": "running",
        "instance_type": "t3.large",
        "availability_zone": "eu-central-1a",
        "private_ip": "10.0.0.10",
        "public_ip": "203.0.113.25",
        "elastic_ip": "203.0.113.25",
        "tags": {"Name": "app-server", "Environment": "prod"},
        "last_refresh": datetime(2026, 1, 1, tzinfo=UTC),
    }
    data.update(overrides)
    return Ec2Instance(**data)
