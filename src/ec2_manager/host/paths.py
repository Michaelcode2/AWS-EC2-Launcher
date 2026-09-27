from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

APP_DIR_NAME = "Ec2DesktopManager"
EXAMPLE_PROFILE_NAME = "example-profile.toml"


def user_data_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / APP_DIR_NAME
        return Path.home() / "AppData" / "Local" / APP_DIR_NAME
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / APP_DIR_NAME
    return Path.home() / ".local" / "share" / APP_DIR_NAME


def log_file_path() -> Path:
    return user_data_dir() / "logs" / "app.log"


def user_config_dir() -> Path:
    return user_data_dir() / "config"


def _is_compiled_bundle() -> bool:
    if getattr(sys, "frozen", False):
        return True
    # Nuitka sets __compiled__ on each compiled module (not sys.frozen).
    return "__compiled__" in globals()


def bundled_config_dir(*, compiled: bool | None = None) -> Path:
    use_bundle = _is_compiled_bundle() if compiled is None else compiled
    if use_bundle:
        return Path(sys.executable).resolve().parent / "config"
    return Path(__file__).resolve().parents[3] / "config"


def ensure_user_config(example_source: Path | None = None) -> Path:
    """Create the per-user config directory and seed the example profile when empty."""
    config_dir = user_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    if any(config_dir.glob("*.toml")):
        return config_dir

    source = example_source or (bundled_config_dir() / EXAMPLE_PROFILE_NAME)
    if not source.is_file():
        return config_dir

    destination = config_dir / EXAMPLE_PROFILE_NAME
    shutil.copy2(source, destination)
    return config_dir
