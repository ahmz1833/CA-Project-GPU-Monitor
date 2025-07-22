from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QGroupBox)

from App.widgets.ToolBar import ToolBar


class MainLayout(QVBoxLayout):
    def __init__(self, title):
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)

        self.toolbar = ToolBar(title)
        self.toolbar.setContentsMargins(0, 0, 0, 0)
        self.addWidget(self.toolbar)

        self.main_h_layout = QHBoxLayout()
        self.main_h_layout.setContentsMargins(10, 10, 10, 10)

        self.left_panel = QFrame()
        self.left_panel.setFrameShape(QFrame.Shape.StyledPanel)
        self.left_panel.setFixedWidth(380)
        self.left_v_layout = QVBoxLayout(self.left_panel)
        self.left_v_layout.setSpacing(0)

        self.params_group = QGroupBox("Parameters")
        self.params_v_layout = QVBoxLayout()
        self.params_v_layout.setSpacing(10)
        self.params_group.setLayout(self.params_v_layout)
        self.left_v_layout.addWidget(self.params_group)
        self.left_v_layout.addStretch()

        self.buttons_h_layout = QHBoxLayout()
        self.left_v_layout.addLayout(self.buttons_h_layout)

        self.right_panel = QWidget()
        self.right_v_layout = QVBoxLayout(self.right_panel)

        self.results_container = QWidget()
        self.results_v_layout = QVBoxLayout(self.results_container)
        self.results_v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_v_layout.addWidget(self.results_container, stretch=1)

        self.main_content_area = None

        self.main_h_layout.addWidget(self.left_panel)
        self.main_h_layout.addWidget(self.right_panel)
        self.addLayout(self.main_h_layout)

    def add_parameter_widget(self, widget):
        self.params_v_layout.addWidget(widget)

    def add_parameter_layout(self, layout):
        self.params_v_layout.addLayout(layout)

    def add_button(self, button, role=None):
        if role == "success":
            button.setProperty("class", "success")
        elif role == "danger":
            button.setProperty("class", "danger")
        self.buttons_h_layout.addWidget(button)

    def set_results_widget(self, widget):
        self._clear_layout(self.results_v_layout)
        self.results_v_layout.addWidget(widget)

    def set_main_content(self, widget):
        if self.main_content_area:
            self.right_v_layout.removeWidget(self.main_content_area)
            self.main_content_area.deleteLater()
        self.main_content_area = widget
        self.right_v_layout.addWidget(widget, stretch=9)

    @property
    def toolbar_layout(self):
        return self.toolbar.layout()

    @property
    def parameters_layout(self):
        return self.params_v_layout

    @property
    def buttons_layout(self):
        return self.buttons_h_layout

    @property
    def results_layout(self):
        return self.results_v_layout

    @property
    def main_content_layout(self):
        return self.right_v_layout

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
