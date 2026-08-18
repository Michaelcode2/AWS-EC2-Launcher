from __future__ import annotations

from boto3.session import Session


def create_session(*, profile_name: str, region_name: str) -> Session:
    if not region_name:
        raise ValueError("Select or configure an AWS region.")
    return Session(profile_name=profile_name, region_name=region_name)
