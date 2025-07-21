from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout

from App.widgets.Label import Label
from App.widgets.ToggleSwitch import ToggleSwitch


class TwoSwitch(QWidget):

    def __init__(self, a_label, b_label, switch_width=70, switch_height=30, parent=None):
        super().__init__(parent)
        self._switch = None
        self.setup_ui(a_label, b_label, switch_width, switch_height)

    def setup_ui(self, a_label, b_label, switch_width, switch_height):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(Label(a_label))
        self._switch = ToggleSwitch(width=switch_width, height=switch_height, initial_state=1)
        layout.addWidget(self._switch)
        layout.addWidget(Label(b_label, alignment=Qt.AlignmentFlag.AlignLeft, normal=False))

    @property
    def value(self) -> bool:
        return self._switch.is_set()
