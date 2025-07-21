from PIL.ImageQt import ImageQt
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (QLabel, QVBoxLayout, QWidget, QFrame)

import App.utils.Loader
from App.pages.base_page import BasePage
from App.pages.welcome.controller import Controller
from App.utils.Loader import Loader as Ld
from App.widgets.Label import Label
from App.widgets.ProgressBar import ProgressBar


class View(BasePage):
    def __init__(self, router):
        super().__init__(router)
        self.controller = Controller(self, router)

        self.main_frame = QFrame(self)
        self.background = QLabel(self)

        self.progress_bar = ProgressBar()
        self.progress_timer = QTimer(self)
        self.description_label = Label("We're getting everything ready for you...")

        self.add_background_image()
        self._setup_ui()

        # setup web_engine!
        self.web_engine = QWebEngineView(self)
        self.web_engine.setHtml("<html><body>Preloading WebEngine...</body></html>")
        self.web_engine.resize(1, 1)
        self.web_engine.move(-100000, -100000)
        self.web_engine.show()
        QTimer.singleShot(2500, self.cleanup_web_engine)

    def cleanup_web_engine(self):
        self.web_engine.hide()
        self.web_engine.deleteLater()

    def add_background_image(self):
        pil_image = Ld.load_image(f"logo/1_{'dark' if App.utils.Loader.Loader.is_dark() else 'light'}.png")
        q_image = ImageQt(pil_image)
        pixmap = QPixmap.fromImage(q_image)
        self.background.setPixmap(pixmap)
        self.background.setScaledContents(True)
        self.background.setGeometry(0, 0, self.width(), self.height())
        self.main_frame.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        self.background.lower()

    def resizeEvent(self, event):
        self.background.setGeometry(0, 0, self.width(), self.height())
        self.main_frame.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self.main_frame)
        main_layout.setContentsMargins(0, 0, 0, 30)
        main_layout.setSpacing(0)

        main_layout.addStretch()

        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(20, 20, 20, 20)
        bottom_layout.setSpacing(10)

        bottom_layout.addWidget(self.description_label)
        bottom_layout.addWidget(self.progress_bar)

        main_layout.addWidget(bottom_widget)

        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(30)

    def update_progress(self):
        current_value = self.progress_bar.value()
        if current_value < 100:
            self.progress_bar.setValue(current_value + 1)
        else:
            self.progress_timer.stop()

            self.controller.skip_welcome()
