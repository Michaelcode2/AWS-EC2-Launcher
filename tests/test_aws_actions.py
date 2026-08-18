from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

from ec2_manager.aws.actions import reboot_instance, start_instance, stop_instance, wait_for_state
from ec2_manager.aws.errors import AwsUserError, InstanceNotInInventoryError

INVENTORY = {"i-0123456789abcdef0"}


def _client_error(code: str, operation: str = "StopInstances") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, operation)


def test_start_requires_inventory() -> None:
    client = Mock()
    with pytest.raises(InstanceNotInInventoryError):
        start_instance(client, "i-unknown", INVENTORY)
    client.start_instances.assert_not_called()


def test_start_success() -> None:
    client = Mock()
    start_instance(client, "i-0123456789abcdef0", INVENTORY)
    client.start_instances.assert_called_once_with(InstanceIds=["i-0123456789abcdef0"])


def test_stop_access_denied_not_retried() -> None:
    client = Mock()
    client.stop_instances.side_effect = _client_error("AccessDenied")
    with pytest.raises(AwsUserError, match="does not allow Stop"):
        stop_instance(client, "i-0123456789abcdef0", INVENTORY)
    assert client.stop_instances.call_count == 1


def test_reboot_not_stop_start() -> None:
    client = Mock()
    reboot_instance(client, "i-0123456789abcdef0", INVENTORY)
    client.reboot_instances.assert_called_once_with(InstanceIds=["i-0123456789abcdef0"])
    client.stop_instances.assert_not_called()
    client.start_instances.assert_not_called()


def test_invalid_state() -> None:
    client = Mock()
    client.stop_instances.side_effect = _client_error("IncorrectInstanceState")
    with pytest.raises(AwsUserError, match="not valid for the current instance state"):
        stop_instance(client, "i-0123456789abcdef0", INVENTORY)
    assert client.stop_instances.call_count == 1


def test_network_timeout() -> None:
    client = Mock()
    client.stop_instances.side_effect = EndpointConnectionError(
        endpoint_url="https://ec2.amazonaws.com"
    )
    with pytest.raises(AwsUserError, match="could not be reached"):
        stop_instance(client, "i-0123456789abcdef0", INVENTORY)
    assert client.stop_instances.call_count == 1


def test_wait_timeout() -> None:
    client = Mock()
    paginator = Mock()
    paginator.paginate.return_value = [
        {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-0123456789abcdef0",
                            "State": {"Name": "pending"},
                            "InstanceType": "t3.micro",
                            "Placement": {},
                            "Tags": [],
                            "NetworkInterfaces": [],
                        }
                    ]
                }
            ]
        }
    ]
    client.get_paginator.return_value = paginator
    start = datetime(2026, 1, 1, tzinfo=UTC)
    ticks = {"n": 0}

    def clock() -> datetime:
        ticks["n"] += 1
        return start + timedelta(seconds=ticks["n"] * 100)

    sleeps: list[float] = []
    with pytest.raises(Exception, match="Timed out"):
        wait_for_state(
            client,
            "i-0123456789abcdef0",
            "running",
            sleep=sleeps.append,
            clock=clock,
            first_wait=5,
            interval=15,
            max_wait=10,
        )
    assert sleeps[0] == 5
