from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLabel

import App.utils.Loader


class Label(QLabel):
    def __init__(self, text="", parent=None,
                 alignment=Qt.AlignmentFlag.AlignCenter,
                 color=None,
                 italic=False,
                 normal=True
                 ):
        super().__init__(text, parent)
        self.setAlignment(alignment)
        if not normal:
            self.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        if not color:
            is_dark = App.utils.Loader.Loader.is_dark()
            color = "white" if is_dark else "red"

        # Convert QColor to string if a QColor was passed
        if isinstance(color, QColor):
            color = color.name()

        self.setStyleSheet(f"""
            color: {color};
            {'font-style: italic;' if italic else ''}""")
