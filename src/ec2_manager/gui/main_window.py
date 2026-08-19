from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from ec2_manager.app import (
    AppSession,
    connect_rdp,
    instance_rdp_enabled,
    logout,
    refresh_inventory,
    restart_selected,
    start_selected,
    stop_selected,
)
from ec2_manager.aws.inventory import Ec2Instance
from ec2_manager.aws.session import create_session
from ec2_manager.gui.dialogs import confirm_restart, confirm_start, confirm_stop
from ec2_manager.gui.instance_table import InstanceTable
from ec2_manager.gui.presentation import shorten_iam_arn
from ec2_manager.gui.widgets import InstanceSummaryPanel, style_action_button
from ec2_manager.gui.workers import FunctionWorker
from ec2_manager.rdp.launcher import select_rdp_address
from ec2_manager.state_logic import RESTART, START, STOP, is_action_enabled, is_action_visible

COMMON_REGIONS = (
    "eu-central-1",
    "eu-west-1",
    "us-east-1",
    "us-west-2",
    "ap-southeast-1",
)


class MainWindow(QWidget):
    def __init__(
        self,
        session: AppSession,
        on_logout: Callable[[], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("EC2 Desktop Manager")
        self._session = session
        self._on_logout = on_logout
        self._worker: FunctionWorker | None = None

        self.profile_label = QLabel(session.profile.application.name)
        self.profile_label.setObjectName("appTitle")

        self.account_badge = QLabel(f"Account {session.identity.account}")
        self.account_badge.setObjectName("accountBadge")

        self.identity_label = QLabel(shorten_iam_arn(session.identity.arn))
        self.identity_label.setObjectName("identityLabel")
        self.identity_label.setToolTip(session.identity.arn)
        self.identity_label.setAccessibleDescription(session.identity.arn)

        self.region_combo = QComboBox()
        for region in _regions(session.region):
            self.region_combo.addItem(region)
        self.region_combo.setCurrentText(session.region)
        self.region_combo.currentTextChanged.connect(self._change_region)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._refresh)
        style_action_button(
            self.refresh_button,
            object_name="btnHeader",
            icon=QStyle.StandardPixmap.SP_BrowserReload,
        )

        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self._logout)
        style_action_button(
            self.logout_button,
            object_name="btnHeader",
            icon=QStyle.StandardPixmap.SP_DialogCloseButton,
        )

        self.table = InstanceTable()
        self.table.itemSelectionChanged.connect(self._sync_actions)

        self.summary = InstanceSummaryPanel()

        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.restart_button = QPushButton("Restart")
        self.rdp_button = QPushButton("Connect RDP")
        style_action_button(
            self.start_button,
            object_name="btnPrimary",
            icon=QStyle.StandardPixmap.SP_MediaPlay,
        )
        style_action_button(
            self.stop_button,
            object_name="btnDanger",
            icon=QStyle.StandardPixmap.SP_MediaStop,
        )
        style_action_button(
            self.restart_button,
            object_name="btnSecondary",
            icon=QStyle.StandardPixmap.SP_BrowserReload,
        )
        style_action_button(
            self.rdp_button,
            object_name="btnSecondary",
            icon=QStyle.StandardPixmap.SP_ComputerIcon,
        )
        self.start_button.clicked.connect(lambda: self._act("start"))
        self.stop_button.clicked.connect(lambda: self._act("stop"))
        self.restart_button.clicked.connect(lambda: self._act("restart"))
        self.rdp_button.clicked.connect(self._connect_rdp)

        self.status = QPlainTextEdit()
        self.status.setObjectName("activityLog")
        self.status.setReadOnly(True)
        self.status.setMinimumHeight(120)
        self.status.setMaximumHeight(160)

        self._build_layout()
        self._apply_feature_flags()
        self.table.set_instances(session.inventory)
        self._append_status("Signed in.")

        interval_ms = max(5, session.profile.application.refresh_interval_seconds) * 1000
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(interval_ms)
        self.resize(1100, 720)

    def _build_layout(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        header = QVBoxLayout()
        title_row = QHBoxLayout()
        title_row.addWidget(self.profile_label)
        title_row.addWidget(self.account_badge)
        title_row.addStretch(1)
        title_row.addWidget(self.refresh_button)
        title_row.addWidget(self.logout_button)
        header.addLayout(title_row)

        meta_row = QHBoxLayout()
        meta_row.addWidget(self.identity_label, 1)
        region_label = QLabel("Region")
        region_label.setObjectName("fieldLabel")
        meta_row.addWidget(region_label)
        meta_row.addWidget(self.region_combo)
        header.addLayout(meta_row)
        root.addLayout(header)

        root.addWidget(self.table, 1)
        root.addWidget(self.summary)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(self.start_button)
        actions.addWidget(self.stop_button)
        actions.addWidget(self.restart_button)
        actions.addWidget(self.rdp_button)
        actions.addStretch(1)
        root.addLayout(actions)

        status_box = QGroupBox("Activity")
        status_box.setObjectName("activityPanel")
        status_layout = QVBoxLayout(status_box)
        status_layout.addWidget(self.status)
        root.addWidget(status_box)

    def _apply_feature_flags(self) -> None:
        features = self._session.profile.features
        self.start_button.setVisible(is_action_visible(START, features))
        self.stop_button.setVisible(is_action_visible(STOP, features))
        self.restart_button.setVisible(is_action_visible(RESTART, features))
        self.rdp_button.setVisible(self._session.profile.rdp.enabled)

    def _selected(self) -> Ec2Instance | None:
        return self.table.selected_instance()

    def _sync_actions(self) -> None:
        instance = self._selected()
        features = self._session.profile.features
        in_flight = bool(instance and instance.instance_id in self._session.in_flight)
        state = instance.state if instance else ""
        self.start_button.setEnabled(
            is_action_enabled(
                START,
                state,
                in_flight=in_flight,
                visible=is_action_visible(START, features),
            )
        )
        self.stop_button.setEnabled(
            is_action_enabled(
                STOP,
                state,
                in_flight=in_flight,
                visible=is_action_visible(STOP, features),
            )
        )
        self.restart_button.setEnabled(
            is_action_enabled(
                RESTART,
                state,
                in_flight=in_flight,
                visible=is_action_visible(RESTART, features),
            )
        )
        self.rdp_button.setEnabled(
            instance is not None and instance_rdp_enabled(self._session, instance)
        )
        if instance:
            address = select_rdp_address(instance, self._session.profile.rdp) or ""
            elastic = instance.elastic_ip or address or "-"
            self.summary.show_instance(instance, elastic_display=elastic)
        else:
            self.summary.show_empty()

    def _busy(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def _run(self, fn: Callable[[], Any], on_success: Callable[[Any], None]) -> None:
        if self._busy():
            return
        self._set_busy(True)
        self._worker = FunctionWorker(fn, self)
        self._worker.succeeded.connect(on_success)
        self._worker.failed.connect(self._failed)
        self._worker.finished.connect(lambda: self._set_busy(False))
        self._worker.start()

    def _set_busy(self, busy: bool) -> None:
        self.refresh_button.setEnabled(not busy)
        if busy:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.restart_button.setEnabled(False)
            self.rdp_button.setEnabled(False)
        else:
            self._sync_actions()

    def _change_region(self, region: str) -> None:
        if not region or region == self._session.region or self._busy():
            return
        self._session.region = region
        self._session.session = create_session(
            profile_name=self._session.profile.aws.profile,
            region_name=region,
        )
        self._append_status(f"Region set to {region}.")
        self._refresh()

    def _refresh(self) -> None:
        if self._busy():
            return
        self._append_status("Refreshing inventory...")
        self._run(lambda: refresh_inventory(self._session), self._on_refreshed)

    def _on_refreshed(self, instances: object) -> None:
        if isinstance(instances, list):
            self.table.set_instances(instances)
        self._append_status("Inventory updated.")
        self._sync_actions()

    def _act(self, action: str) -> None:
        instance = self._selected()
        if instance is None or self._busy():
            return
        if action == "stop" and not confirm_stop(self, instance.name):
            return
        if action == "restart" and not confirm_restart(self, instance.name):
            return
        if (
            action == "start"
            and self._session.profile.application.confirm_start
            and not confirm_start(self, instance.name)
        ):
            return
        self._session.in_flight.add(instance.instance_id)
        self._sync_actions()
        self._append_status(f"{action.title()} requested for {instance.instance_id}.")
        calls = {
            "start": lambda: start_selected(self._session, instance.instance_id, sleep=time.sleep),
            "stop": lambda: stop_selected(self._session, instance.instance_id, sleep=time.sleep),
            "restart": lambda: restart_selected(
                self._session, instance.instance_id, sleep=time.sleep
            ),
        }
        self._run(calls[action], lambda _: self._action_done(action, instance.instance_id))

    def _action_done(self, action: str, instance_id: str) -> None:
        self.table.set_instances(self._session.inventory)
        self._append_status(f"{action.title()} finished for {instance_id}.")
        self._sync_actions()

    def _connect_rdp(self) -> None:
        instance = self._selected()
        if instance is None:
            return
        try:
            address = connect_rdp(self._session, instance)
            self._append_status(f"Launched RDP to {address}.")
        except Exception as exc:  # noqa: BLE001
            self._append_status(str(exc))

    def _failed(self, message: str) -> None:
        self._append_status(message)
        self.table.set_instances(self._session.inventory)
        self._sync_actions()

    def _logout(self) -> None:
        self._timer.stop()
        logout(self._session)
        self.close()
        self._on_logout()

    def _append_status(self, message: str) -> None:
        self.status.appendPlainText(message)


def _regions(current: str) -> list[str]:
    values = list(COMMON_REGIONS)
    if current not in values:
        values.insert(0, current)
    return values
