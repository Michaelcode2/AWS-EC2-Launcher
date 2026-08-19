from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from ec2_manager.aws.inventory import Ec2Instance
from ec2_manager.gui.widgets import apply_state_item_colors

COLUMNS = (
    "Name",
    "Instance ID",
    "State",
    "Instance type",
    "Availability Zone",
    "Private IP",
    "Public IP",
    "Elastic IP",
    "Environment",
    "Last refresh",
)

STATE_COLUMN = COLUMNS.index("State")


class InstanceTable(QTableWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, len(COLUMNS), parent)
        self.setHorizontalHeaderLabels(COLUMNS)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._instances: list[Ec2Instance] = []

    def set_instances(self, instances: Sequence[Ec2Instance]) -> None:
        selected_id = self.selected_instance_id()
        self._instances = list(instances)
        self.setRowCount(len(self._instances))
        restore_row = 0
        for row, instance in enumerate(self._instances):
            values = _row_values(instance)
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                if column == STATE_COLUMN:
                    apply_state_item_colors(item, instance.state)
                self.setItem(row, column, item)
            if instance.instance_id == selected_id:
                restore_row = row
        if self._instances:
            self.selectRow(restore_row)

    def selected_instance(self) -> Ec2Instance | None:
        rows = self.selectionModel().selectedRows() if self.selectionModel() else []
        if not rows:
            return None
        index = rows[0].row()
        if 0 <= index < len(self._instances):
            return self._instances[index]
        return None

    def selected_instance_id(self) -> str | None:
        instance = self.selected_instance()
        return instance.instance_id if instance else None


def _row_values(instance: Ec2Instance) -> tuple[str, ...]:
    refresh = instance.last_refresh.strftime("%Y-%m-%d %H:%M:%S")
    return (
        instance.name,
        instance.instance_id,
        instance.state,
        instance.instance_type,
        instance.availability_zone or "",
        instance.private_ip or "",
        instance.public_ip or "",
        instance.elastic_ip or "",
        instance.tags.get("Environment", instance.tags.get("environment", "")),
        refresh,
    )
