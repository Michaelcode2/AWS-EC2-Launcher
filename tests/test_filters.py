from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock

from ec2_manager.aws.inventory import list_instances
from ec2_manager.config.models import FiltersConfig
from ec2_manager.filters import apply_filters
from tests.helpers import make_instance


def _page(*instances: dict) -> dict:
    return {"Reservations": [{"Instances": list(instances)}]}


def test_pagination_and_name_fallback() -> None:
    named = {
        "InstanceId": "i-aaa",
        "State": {"Name": "running"},
        "InstanceType": "t3.micro",
        "Placement": {"AvailabilityZone": "eu-central-1a"},
        "PrivateIpAddress": "10.0.0.1",
        "PublicIpAddress": "1.1.1.1",
        "Tags": [{"Key": "Name", "Value": "named"}],
        "NetworkInterfaces": [
            {
                "Association": {
                    "PublicIp": "203.0.113.10",
                    "AllocationId": "eipalloc-1",
                    "IpOwnerId": "123456789012",
                }
            }
        ],
    }
    unnamed = {
        "InstanceId": "i-bbb",
        "State": {"Name": "stopped"},
        "InstanceType": "t3.micro",
        "Placement": {"AvailabilityZone": "eu-central-1b"},
        "PrivateIpAddress": "10.0.0.2",
        "Tags": [],
        "NetworkInterfaces": [],
    }
    paginator = Mock()
    paginator.paginate.return_value = [_page(named), _page(unnamed)]
    client = Mock()
    client.get_paginator.return_value = paginator

    now = datetime(2026, 2, 1, tzinfo=UTC)
    instances = list_instances(client, now=now)
    assert [item.instance_id for item in instances] == ["i-aaa", "i-bbb"]
    assert instances[0].name == "named"
    assert instances[1].name == "i-bbb"
    assert instances[0].elastic_ip == "203.0.113.10"
    assert instances[0].last_refresh == now


def test_filter_all() -> None:
    items = [make_instance(instance_id="i-1"), make_instance(instance_id="i-2")]
    assert apply_filters(items, FiltersConfig(mode="all")) == items


def test_filter_instance_ids() -> None:
    items = [make_instance(instance_id="i-1"), make_instance(instance_id="i-2")]
    filtered = apply_filters(items, FiltersConfig(mode="instance_ids", instance_ids=("i-2",)))
    assert [item.instance_id for item in filtered] == ["i-2"]


def test_filter_tags() -> None:
    keep = make_instance(
        instance_id="i-1",
        tags={"ManagedBy": "ec2-desktop-manager", "Customer": "acme"},
    )
    drop = make_instance(instance_id="i-2", tags={"ManagedBy": "other"})
    filtered = apply_filters(
        [keep, drop],
        FiltersConfig(
            mode="tags",
            tags={"ManagedBy": "ec2-desktop-manager", "Customer": "acme"},
        ),
    )
    assert [item.instance_id for item in filtered] == ["i-1"]
