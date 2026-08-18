from __future__ import annotations

from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError, NoCredentialsError

from ec2_manager.aws.errors import (
    AccountMismatchError,
    ExpiredCredentialsError,
    map_aws_error,
)
from ec2_manager.aws.identity import CallerIdentity, get_caller_identity, verify_account


def test_matching_account() -> None:
    identity = CallerIdentity(
        account="123456789012",
        arn="arn:aws:iam::123456789012:user/a",
        user_id="AIDA",
    )
    assert verify_account(identity, "123456789012") is identity


def test_mismatched_account() -> None:
    identity = CallerIdentity(
        account="999999999999",
        arn="arn:aws:iam::999999999999:user/a",
        user_id="AIDA",
    )
    with pytest.raises(AccountMismatchError, match="different AWS account"):
        verify_account(identity, "123456789012")


def test_expired_token_mapping() -> None:
    error = ClientError(
        {"Error": {"Code": "ExpiredToken", "Message": "expired"}},
        "GetCallerIdentity",
    )
    mapped = map_aws_error(error)
    assert isinstance(mapped, ExpiredCredentialsError)
    assert "sign in again" in mapped.message


def test_invalid_access_key_mapping() -> None:
    error = ClientError(
        {"Error": {"Code": "InvalidClientTokenId", "Message": "bad key"}},
        "GetCallerIdentity",
    )
    mapped = map_aws_error(error)
    assert "aws configure" in mapped.message


def test_missing_credentials_mapping() -> None:
    mapped = map_aws_error(NoCredentialsError())
    assert "aws configure" in mapped.message


def test_get_caller_identity() -> None:
    client = Mock()
    client.get_caller_identity.return_value = {
        "Account": "123456789012",
        "Arn": "arn:aws:sts::123456789012:assumed-role/r/s",
        "UserId": "AROASAMPLE:s",
    }
    identity = get_caller_identity(client)
    assert identity.account == "123456789012"
    assert identity.arn.endswith("/s")
