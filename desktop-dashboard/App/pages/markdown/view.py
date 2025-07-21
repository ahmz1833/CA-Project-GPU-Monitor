from PySide6.QtWidgets import QPushButton, QVBoxLayout

from App.pages.base_page import BasePage
from App.pages.markdown.controller import Controller
from App.widgets.MarkdownLabel import MarkdownLabel


class View(BasePage):
    def __init__(self, router):
        super().__init__(router)
        self.controller = Controller(self, router)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        self.label = None
        self.btn = None

    def clear_ui(self):
        if self.label:
            self.label.setParent(None)
            self.label.deleteLater()
            self.label = None

        if self.btn:
            self.btn.setParent(None)
            self.btn.deleteLater()
            self.btn = None

    def _setup_ui(self):
        self.clear_ui()
        self.label = MarkdownLabel(self.controller.path, True)
        self.btn = QPushButton("Back")
        self.btn.clicked.connect(lambda: self.controller.navigate_to_page2())
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.btn)
        self.connect_signals()

        self.label.show()
        self.btn.show()
