from PySide6.QtWidgets import QCheckBox


class CheckBox(QCheckBox):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(30)
