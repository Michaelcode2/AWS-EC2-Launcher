from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "Ec2DesktopManager"


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


def bundled_config_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "config"
    return Path(__file__).resolve().parents[3] / "config"
