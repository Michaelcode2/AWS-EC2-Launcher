from __future__ import annotations

FORBIDDEN_KEYS = {
    "aws_access_key_id",
    "aws_secret_access_key",
    "aws_session_token",
    "secret_access_key",
    "session_token",
    "password",
    "passwd",
    "refresh_token",
    "private_key",
    "windows_password",
}


class ConfigError(ValueError):
    """Raised when a profile file is missing, invalid, or contains secrets."""


def collect_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            keys.add(str(key).lower())
            keys.update(collect_keys(nested))
    elif isinstance(value, list):
        for item in value:
            keys.update(collect_keys(item))
    return keys


def reject_secrets(data: dict[str, object]) -> None:
    found = collect_keys(data) & FORBIDDEN_KEYS
    if found:
        raise ConfigError(
            "Profile contains forbidden secret keys: " + ", ".join(sorted(found))
        )


def require_str(section: dict[str, object], key: str, *, section_name: str) -> str:
    value = section.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{section_name}.{key} is required.")
    return value.strip()


def optional_bool(section: dict[str, object], key: str, default: bool) -> bool:
    value = section.get(key, default)
    if not isinstance(value, bool):
        raise ConfigError(f"{key} must be a boolean.")
    return value


def optional_int(section: dict[str, object], key: str, default: int) -> int:
    value = section.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConfigError(f"{key} must be an integer.")
    return value
