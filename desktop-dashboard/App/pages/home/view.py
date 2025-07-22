from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QPushButton, QVBoxLayout, QMessageBox,
                               QScrollArea, QWidget, QHBoxLayout, QSizePolicy)

import App.widgets.ToolBar
from App.logic.Logic import GPUMonitor
from App.pages.base_page import BasePage
from App.pages.home.controller import Controller
from App.utils.Loader import Loader
from App.widgets.Label import Label
from App.widgets.SingleInput import SingleInput


class View(BasePage):
    def __init__(self, router):
        super().__init__(router)
        self.controller = Controller(self, router)
        self.toolbar = None
        self.help_btn = None
        self._setup_ui()
        self.connect_signals()

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.toolbar = App.widgets.ToolBar.ToolBar("GPU Monitoring")
        main_layout.addWidget(self.toolbar)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        url_label = Label(f"Current URL: {App.logic.Logic.GPUMonitor.URL}")
        url_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(url_label)

        self.tagline = SingleInput("URL", input_type='text')
        container_layout = QHBoxLayout()
        container_layout.addLayout(self.tagline)
        self.apply_button = QPushButton("Apply")
        container_layout.addWidget(self.apply_button)
        content_layout.addLayout(container_layout)

        gpu_label = Label("Available GPUs")
        gpu_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        content_layout.addWidget(gpu_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        button_container = QWidget()
        button_layout = QVBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(5, 5, 5, 5)
        button_container.setLayout(button_layout)

        try:
            monitor = GPUMonitor()
            gpus = monitor.get_gpu_list()
            if not gpus:
                no_gpu_label = Label("No GPUs detected")
                no_gpu_label.setStyleSheet("font-style: italic; color: gray;")
                button_layout.addWidget(no_gpu_label)
            else:
                for gpu_id, gpu_info in gpus.items():
                    btn = QPushButton()
                    btn.setProperty("gpu_id", gpu_id)
                    btn.setProperty("health", gpu_info.get('health', 'unknown').lower())

                    # Format button text with name and UUID
                    btn_text = f"GPU {gpu_id}: {gpu_info.get('name', 'Unknown')}\n"
                    btn_text += f"UUID: {gpu_info.get('uuid', 'N/A')}\n"
                    btn_text += f"Status: {gpu_info.get('health', 'unknown')}"
                    btn.setText(btn_text)

                    health = gpu_info.get('health', 'unknown').lower()
                    if health == 'healthy':
                        pass
                    elif health == 'warning':
                        btn.setProperty("class", "warning")
                    else:
                        btn.setProperty("class", "danger")

                    btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                    btn.setMinimumHeight(80)

                    btn.clicked.connect(lambda checked=False, gid=gpu_id: self.controller.show_gpu_info(gid))

                    button_layout.addWidget(btn)

        except Exception as e:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Icon.Critical)
            error_msg.setText("Failed to get GPU information")
            error_msg.setInformativeText(str(e))
            error_msg.setWindowTitle("Error")
            error_msg.exec()

            error_label = Label("Failed to load GPU information")
            error_label.setStyleSheet("color: red; font-style: italic;")
            button_layout.addWidget(error_label)

        scroll.setWidget(button_container)
        content_layout.addWidget(scroll)

        self.help_btn = QPushButton("about this application")
        self.help_btn.clicked.connect(lambda: self.controller.show_about())
        if Loader().is_dark():
            self.help_btn.setStyleSheet("color: #ffffff;")
        content_layout.addWidget(self.help_btn)

        footer = Label("Made with ❤️ for Computer Architecture Project", italic=True)
        content_layout.addWidget(footer)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

    def connect_signals(self):
        self.apply_button.clicked.connect(lambda checked=False:
                                          self.controller.changeURL(self.tagline.get_value()))
