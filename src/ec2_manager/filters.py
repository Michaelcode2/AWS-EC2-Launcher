from __future__ import annotations

from collections.abc import Sequence

from ec2_manager.aws.inventory import Ec2Instance
from ec2_manager.config.models import FiltersConfig


def apply_filters(instances: Sequence[Ec2Instance], filters: FiltersConfig) -> list[Ec2Instance]:
    if filters.mode == "all":
        return list(instances)
    if filters.mode == "instance_ids":
        allowed = set(filters.instance_ids)
        return [item for item in instances if item.instance_id in allowed]
    return [item for item in instances if _matches_tags(item, filters.tags)]


def _matches_tags(instance: Ec2Instance, required: dict[str, str]) -> bool:
    return all(instance.tags.get(key) == value for key, value in required.items())
