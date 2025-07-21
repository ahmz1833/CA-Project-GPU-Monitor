from PySide6.QtCore import Qt
from PySide6.QtWidgets import QProgressBar


class ProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedHeight(10)
        self.setTextVisible(False)
        self.setRange(0, 100)
        self.setValue(0)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
