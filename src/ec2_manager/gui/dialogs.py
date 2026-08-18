from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget

STOP_WARNING = (
    "Stopping this instance can disconnect active users and may interrupt unsaved work.\n\n"
    "Continue?"
)
RESTART_WARNING = (
    "Restarting this instance reboots the server and can disconnect active users.\n\n"
    "Continue?"
)
START_WARNING = "Start this instance now?"


def confirm_stop(parent: QWidget | None, instance_name: str) -> bool:
    return _confirm(parent, f"Stop {instance_name}?", STOP_WARNING)


def confirm_restart(parent: QWidget | None, instance_name: str) -> bool:
    return _confirm(parent, f"Restart {instance_name}?", RESTART_WARNING)


def confirm_start(parent: QWidget | None, instance_name: str) -> bool:
    return _confirm(parent, f"Start {instance_name}?", START_WARNING)


def _confirm(parent: QWidget | None, title: str, text: str) -> bool:
    result = QMessageBox.question(
        parent,
        title,
        text,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return result == QMessageBox.StandardButton.Yes
