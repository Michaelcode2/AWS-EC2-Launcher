from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from ec2_manager.app import AppSession, login
from ec2_manager.config.models import CustomerProfile
from ec2_manager.gui.widgets import style_action_button
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

        title = QLabel("EC2 Desktop Manager")
        title.setObjectName("appTitle")

        profile_label = QLabel("Customer profile")
        profile_label.setObjectName("fieldLabel")

        self.profile_combo = QComboBox()
        for profile in self._profiles:
            self.profile_combo.addItem(profile.application.name, profile)

        self.status = QLabel("Select a profile and sign in with AWS Identity Center.")
        self.status.setObjectName("helperText")
        self.status.setWordWrap(True)

        self.sign_in = QPushButton("Sign in")
        self.sign_in.clicked.connect(self._start_login)
        style_action_button(
            self.sign_in,
            object_name="btnPrimary",
            icon=QStyle.StandardPixmap.SP_DialogOkButton,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(title)
        row = QHBoxLayout()
        row.addWidget(profile_label)
        row.addWidget(self.profile_combo, 1)
        layout.addLayout(row)
        layout.addWidget(self.status)
        layout.addWidget(self.sign_in, alignment=Qt.AlignmentFlag.AlignLeft)
        self.resize(520, 220)

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
