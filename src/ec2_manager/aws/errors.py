from __future__ import annotations

from botocore.exceptions import (
    ClientError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)

EXPIRED_CODES = {
    "ExpiredToken",
    "ExpiredTokenException",
    "RequestExpired",
}


class AwsUserError(Exception):
    """Error with a short message suitable for the UI."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.retryable = retryable


class AccountMismatchError(AwsUserError):
    def __init__(self, expected: str, actual: str) -> None:
        super().__init__(
            "The selected profile authenticated to a different AWS account."
        )
        self.expected = expected
        self.actual = actual


class ExpiredCredentialsError(AwsUserError):
    def __init__(self) -> None:
        super().__init__("AWS login has expired. Please sign in again.")


class InstanceNotInInventoryError(AwsUserError):
    def __init__(self, instance_id: str) -> None:
        super().__init__(
            "The instance no longer exists or is not visible in this region."
        )
        self.instance_id = instance_id


def is_expired_credentials(exc: BaseException) -> bool:
    name = type(exc).__name__
    if name in {
        "UnauthorizedSSOTokenError",
        "TokenRetrievalError",
        "SSOTokenLoadError",
        "UnauthorizedSSOTokenLoadError",
    }:
        return True
    message = str(exc).lower()
    if "sso" in message and ("expired" in message or "token" in message):
        return True
    if isinstance(exc, ClientError):
        code = exc.response.get("Error", {}).get("Code", "")
        return code in EXPIRED_CODES
    return False


def map_aws_error(exc: BaseException, *, action: str | None = None) -> AwsUserError:
    if isinstance(exc, AwsUserError):
        return exc
    if is_expired_credentials(exc):
        return ExpiredCredentialsError()
    if isinstance(exc, (EndpointConnectionError, ConnectTimeoutError, ReadTimeoutError)):
        return AwsUserError("AWS could not be reached. Check your network connection.")
    if isinstance(exc, ClientError):
        code = str(exc.response.get("Error", {}).get("Code", ""))
        if code in {"AccessDenied", "UnauthorizedOperation", "AccessDeniedException"}:
            if action:
                return AwsUserError(
                    f"AWS policy does not allow {action} for this instance. "
                    "Contact the AWS administrator if this operation is required."
                )
            return AwsUserError("Your AWS policy does not allow this operation.")
        if code in {"InvalidInstanceID.NotFound", "InvalidInstanceID.Malformed"}:
            return AwsUserError(
                "The instance no longer exists or is not visible in this region."
            )
        if code in {"IncorrectInstanceState", "InvalidInstanceState"}:
            return AwsUserError(
                "The requested action is not valid for the current instance state."
            )
        if code in EXPIRED_CODES:
            return ExpiredCredentialsError()
    return AwsUserError("AWS could not complete the request. Check the application log.")
