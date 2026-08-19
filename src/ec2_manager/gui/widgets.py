from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStyle,
    QWidget,
)

from ec2_manager.aws.inventory import Ec2Instance
from ec2_manager.gui.presentation import StateStyle, instance_state_style


def style_action_button(
    button: QPushButton,
    *,
    object_name: str,
    icon: QStyle.StandardPixmap,
) -> None:
    button.setObjectName(object_name)
    style = QApplication.style()
    if style is not None:
        button.setIcon(style.standardIcon(icon))


def apply_state_badge(label: QLabel, state: str, style: StateStyle | None = None) -> None:
    resolved = style or instance_state_style(state)
    label.setText(state)
    label.setStyleSheet(
        f"background-color: {resolved.background};"
        f" color: {resolved.foreground};"
        " padding: 2px 10px;"
        " border-radius: 4px;"
        " font-weight: 600;"
        " font-size: 12px;"
    )


def apply_state_item_colors(item: object, state: str) -> None:
    from PySide6.QtWidgets import QTableWidgetItem

    if not isinstance(item, QTableWidgetItem):
        return
    style = instance_state_style(state)
    item.setForeground(QColor(style.foreground))
    item.setBackground(QColor(style.background))


class InstanceSummaryPanel(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("summaryPanel")

        self._empty = QLabel("Select an instance to view details.")
        self._empty.setObjectName("summaryMeta")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._content = QWidget()
        content_layout = QGridLayout(self._content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setHorizontalSpacing(8)
        content_layout.setVerticalSpacing(4)

        self._name = QLabel()
        self._name.setObjectName("summaryName")
        self._state = QLabel()
        self._state.setObjectName("stateBadge")
        self._id = QLabel()
        self._id.setObjectName("summaryMeta")
        self._type = QLabel()
        self._type.setObjectName("summaryMeta")
        self._private = QLabel()
        self._private.setObjectName("summaryMeta")
        self._public = QLabel()
        self._public.setObjectName("summaryMeta")
        self._elastic = QLabel()
        self._elastic.setObjectName("summaryMeta")

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.addWidget(self._name)
        title_row.addWidget(self._state)
        title_row.addStretch(1)
        content_layout.addLayout(title_row, 0, 0, 1, 2)
        content_layout.addWidget(self._meta_label("Instance ID"), 1, 0)
        content_layout.addWidget(self._id, 1, 1)
        content_layout.addWidget(self._meta_label("Type"), 2, 0)
        content_layout.addWidget(self._type, 2, 1)
        content_layout.addWidget(self._meta_label("Private IP"), 3, 0)
        content_layout.addWidget(self._private, 3, 1)
        content_layout.addWidget(self._meta_label("Public IP"), 4, 0)
        content_layout.addWidget(self._public, 4, 1)
        content_layout.addWidget(self._meta_label("Elastic IP"), 5, 0)
        content_layout.addWidget(self._elastic, 5, 1)

        root = QHBoxLayout(self)
        root.setContentsMargins(8, 6, 8, 6)
        root.addWidget(self._empty)
        root.addWidget(self._content)
        self._content.hide()
        self.show_empty()

    @staticmethod
    def _meta_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def show_empty(self) -> None:
        self._empty.show()
        self._content.hide()

    def show_instance(self, instance: Ec2Instance, *, elastic_display: str) -> None:
        self._empty.hide()
        self._content.show()
        self._name.setText(instance.name)
        apply_state_badge(self._state, instance.state)
        self._id.setText(instance.instance_id)
        self._type.setText(instance.instance_type)
        self._private.setText(instance.private_ip or "-")
        self._public.setText(instance.public_ip or "-")
        self._elastic.setText(elastic_display or "-")
