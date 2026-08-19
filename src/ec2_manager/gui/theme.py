from __future__ import annotations

from importlib import resources

from PySide6.QtWidgets import QApplication

from ec2_manager.logging_config import get_logger

log = get_logger()


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    try:
        qss_path = resources.files("ec2_manager.gui.assets").joinpath("theme.qss")
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, TypeError, ValueError) as exc:
        log.warning("Could not load theme stylesheet: %s", exc)
