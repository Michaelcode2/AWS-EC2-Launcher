from __future__ import annotations

import sys
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication, QMessageBox

from ec2_manager.app import AppSession
from ec2_manager.config.loader import load_profiles
from ec2_manager.config.models import CustomerProfile
from ec2_manager.config.validation import ConfigError
from ec2_manager.gui.login_window import LoginWindow
from ec2_manager.gui.main_window import MainWindow
from ec2_manager.logging_config import configure_logging, get_logger
from ec2_manager.platform.paths import user_config_dir


def main() -> int:
    configure_logging()
    log = get_logger()
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("EC2 Desktop Manager")
    user_config_dir().mkdir(parents=True, exist_ok=True)

    try:
        profiles = load_profiles()
    except ConfigError as exc:
        QMessageBox.critical(None, "Configuration error", str(exc))
        return 1
    if not profiles:
        QMessageBox.critical(
            None,
            "Configuration error",
            "No customer profiles were found. "
            "Add a TOML profile under the configuration directory.",
        )
        return 1

    shell = _Shell(qt_app, profiles)
    shell.show_login()
    log.info("application_started")
    return qt_app.exec()


class _Shell:
    def __init__(self, qt_app: QApplication, profiles: Sequence[CustomerProfile]) -> None:
        self._qt_app = qt_app
        self._profiles = profiles
        self._login: LoginWindow | None = None
        self._main: MainWindow | None = None

    def show_login(self) -> None:
        self._login = LoginWindow(self._profiles, self._open_main)
        self._login.show()

    def _open_main(self, session: AppSession) -> None:
        self._main = MainWindow(session, on_logout=self.show_login)
        self._main.show()


if __name__ == "__main__":
    raise SystemExit(main())
