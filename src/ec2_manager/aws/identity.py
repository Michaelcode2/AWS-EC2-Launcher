from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound

from ec2_manager.aws.errors import AccountMismatchError, map_aws_error


@dataclass(frozen=True)
class CallerIdentity:
    account: str
    arn: str
    user_id: str


def get_caller_identity(sts_client: Any) -> CallerIdentity:
    try:
        response = sts_client.get_caller_identity()
    except (ClientError, NoCredentialsError, ProfileNotFound) as exc:
        raise map_aws_error(exc) from exc
    return CallerIdentity(
        account=str(response["Account"]),
        arn=str(response["Arn"]),
        user_id=str(response["UserId"]),
    )


def verify_account(identity: CallerIdentity, expected_account_id: str) -> CallerIdentity:
    if identity.account != expected_account_id:
        raise AccountMismatchError(expected_account_id, identity.account)
    return identity
