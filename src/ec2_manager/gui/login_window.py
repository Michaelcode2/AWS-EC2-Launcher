from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ec2_manager.app import AppSession, login
from ec2_manager.config.models import CustomerProfile
from ec2_manager.gui.workers import FunctionWorker


class LoginWindow(QWidget):
    def __init__(
        self,
        profiles: Sequence[CustomerProfile],
        on_logged_in: Callable[[AppSession], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("EC2 Desktop Manager")
        self._profiles = list(profiles)
        self._on_logged_in = on_logged_in
        self._worker: FunctionWorker | None = None

        self.profile_combo = QComboBox()
        for profile in self._profiles:
            self.profile_combo.addItem(profile.application.name, profile)

        self.status = QLabel("Select a profile and sign in.")
        self.status.setWordWrap(True)
        self.sign_in = QPushButton("Sign in")
        self.sign_in.clicked.connect(self._start_login)

        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        row.addWidget(QLabel("Customer profile"))
        row.addWidget(self.profile_combo, 1)
        layout.addLayout(row)
        layout.addWidget(self.sign_in)
        layout.addWidget(self.status)
        self.resize(520, 180)

    def selected_profile(self) -> CustomerProfile | None:
        data = self.profile_combo.currentData()
        return data if isinstance(data, CustomerProfile) else None

    def _start_login(self) -> None:
        profile = self.selected_profile()
        if profile is None:
            QMessageBox.warning(self, "Profile", "Select a customer profile.")
            return
        self.sign_in.setEnabled(False)
        self.status.setText(
            "Signing in. Complete the browser prompt if AWS CLI opens one."
        )
        self._worker = FunctionWorker(lambda: login(profile), self)
        self._worker.succeeded.connect(self._login_ok)
        self._worker.failed.connect(self._login_failed)
        self._worker.start()

    def _login_ok(self, session: object) -> None:
        self.sign_in.setEnabled(True)
        if isinstance(session, AppSession):
            self._on_logged_in(session)
            self.close()

    def _login_failed(self, message: str) -> None:
        self.sign_in.setEnabled(True)
        self.status.setText(message)
        QMessageBox.critical(self, "Sign in failed", message)
