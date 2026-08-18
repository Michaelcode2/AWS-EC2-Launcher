from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from botocore.exceptions import ClientError

from ec2_manager.aws.errors import map_aws_error


@dataclass
class Ec2Instance:
    instance_id: str
    name: str
    state: str
    instance_type: str
    availability_zone: str | None
    private_ip: str | None
    public_ip: str | None
    elastic_ip: str | None
    tags: dict[str, str] = field(default_factory=dict)
    last_refresh: datetime = field(default_factory=lambda: datetime.now(UTC))


def list_instances(ec2_client: Any, *, now: datetime | None = None) -> list[Ec2Instance]:
    refreshed_at = now or datetime.now(UTC)
    instances: list[Ec2Instance] = []
    try:
        paginator = ec2_client.get_paginator("describe_instances")
        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for raw in reservation.get("Instances", []):
                    instances.append(_from_api(raw, refreshed_at))
    except ClientError as exc:
        raise map_aws_error(exc) from exc
    return instances


def _from_api(raw: dict[str, Any], refreshed_at: datetime) -> Ec2Instance:
    tags = {str(tag["Key"]): str(tag["Value"]) for tag in raw.get("Tags", []) if "Key" in tag}
    instance_id = str(raw["InstanceId"])
    name = tags.get("Name") or instance_id
    state = str(raw.get("State", {}).get("Name", "unknown"))
    placement = raw.get("Placement") or {}
    public_ip = raw.get("PublicIpAddress")
    elastic_ip = _elastic_ip(raw) or None
    return Ec2Instance(
        instance_id=instance_id,
        name=name,
        state=state,
        instance_type=str(raw.get("InstanceType", "")),
        availability_zone=placement.get("AvailabilityZone"),
        private_ip=raw.get("PrivateIpAddress"),
        public_ip=str(public_ip) if public_ip else None,
        elastic_ip=elastic_ip,
        tags=tags,
        last_refresh=refreshed_at,
    )


def _elastic_ip(raw: dict[str, Any]) -> str | None:
    for interface in raw.get("NetworkInterfaces", []):
        association = interface.get("Association") or {}
        public_ip = association.get("PublicIp")
        if not public_ip:
            continue
        owner = str(association.get("IpOwnerId", ""))
        allocation = association.get("AllocationId")
        if allocation or (owner and owner != "amazon"):
            return str(public_ip)
    return None
