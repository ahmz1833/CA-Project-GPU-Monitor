import os
import sys

from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLabel,
                               QPushButton, QMessageBox, QApplication, QVBoxLayout, QFrame)

from App.navigation.router import Router
from App.utils.Loader import Loader
from App.widgets.ToggleSwitch import ToggleSwitch


class _ToolbarWithOutLine(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self._title = title
        if Loader.is_dark():
            self._bg_color = QColor("#1a237e")
        else:
            self._bg_color = QColor("#ffd6e7")
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        title_label = QLabel(self._title)
        title_label.setStyleSheet("font-weight: bold; font-size: 20px;")
        layout.addWidget(title_label)

        layout.addStretch()

        theme_container = QWidget()
        theme_layout = QHBoxLayout(theme_container)
        theme_layout.setContentsMargins(10, 5, 10, 5)
        theme_layout.setSpacing(10)

        theme_container.setStyleSheet(f"background-color: {self._bg_color.name()}; border-radius: 8px;")

        light_label = QLabel("☀️")
        dark_label = QLabel("🌙")

        light_label.setStyleSheet("font-size: 24px; color: gold;")
        dark_label.setStyleSheet("font-size: 24px; color: silver;")

        self.theme_toggle = ToggleSwitch(initial_state=Loader.is_dark(), show_border=True)

        theme_layout.addWidget(light_label)
        theme_layout.addWidget(self.theme_toggle)
        theme_layout.addWidget(dark_label)

        self.apply_button = QPushButton("Apply")
        self.apply_button.setFixedWidth(65)
        normal_color = "#ffffff" if not Loader.is_dark() else "#f0f0f0"
        hover_color = "#f0f0f0" if not Loader.is_dark() else "#ffffff"

        self.apply_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {normal_color};
                color: black;
                border: none;
                border-radius: 20px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: #e0e0e0;
            }}
        """)
        self.apply_button.clicked.connect(self.change_theme)

        theme_layout.addWidget(self.apply_button)

        layout.addWidget(theme_container)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._bg_color)

    def is_dark(self):
        return self.theme_toggle.is_set()

    def change_theme(self):
        new_theme = self.theme_toggle.is_set()
        loader = Loader()
        current_theme_is_dark = loader.is_dark()

        if new_theme == current_theme_is_dark:
            self._notify_theme_unchanged(new_theme)
            return

        self._apply_new_theme(loader, new_theme)
        self._restart_application()

    @staticmethod
    def _notify_theme_unchanged(is_dark_theme):
        theme_name = "dark" if is_dark_theme else "light"
        QMessageBox.information(
            None,
            "No Change Needed",
            f"The application is already in {theme_name} mode."
        )

    @staticmethod
    def _apply_new_theme(loader, is_dark_theme):
        theme_value = "dark" if is_dark_theme else "light"
        loader.save_json("theme", {'theme': theme_value}, False)
        loader.destroy_instance()
        Router.instance().clear_instance()

    @staticmethod
    def _restart_application():
        QApplication.quit()
        os.execv(sys.executable, [sys.executable] + sys.argv)


class ToolBar(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toolbar = _ToolbarWithOutLine(title)
        layout.addWidget(self.toolbar)

        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.separator.setStyleSheet("color: #cccccc;")
        layout.addWidget(self.separator)

        self.setLayout(layout)
