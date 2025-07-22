from PySide6.QtWidgets import QFrame


class Separator(QFrame):
    def __init__(self, orientation: str = 'horizontal', parent=None):
        super().__init__(parent)

        if orientation == 'horizontal':
            self.setFrameShape(QFrame.Shape.HLine)
        elif orientation == 'vertical':
            self.setFrameShape(QFrame.Shape.VLine)
        else:
            raise ValueError("Orientation must be 'horizontal' or 'vertical'")

        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setLineWidth(1)

        if orientation == 'horizontal':
            self.setMinimumHeight(2)
        else:
            self.setMinimumWidth(2)
