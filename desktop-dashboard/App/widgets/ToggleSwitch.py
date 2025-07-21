from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal, Property
from PySide6.QtGui import QPainter, QBrush, QColor
from PySide6.QtWidgets import QWidget

import App.utils.Loader


class ToggleSwitch(QWidget):
    theme_changed = Signal(bool)

    def __init__(self, width=80, height=40, initial_state=False, show_border=False, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)

        self._is_dark = initial_state
        self._thumb_pos = 1.0 if initial_state else 0.0
        self._show_border = show_border

        if App.utils.Loader.Loader.is_dark():
            self._bg_light = QColor(166, 245, 243)
            self._bg_dark = QColor(53, 91, 242)
            self._thumb_color = QColor(100, 149, 237)
        else:
            self._bg_light = QColor(252, 202, 210)
            self._bg_dark = QColor(255, 107, 129)
            self._thumb_color = QColor(184, 68, 85)

        self._anim = QPropertyAnimation(self, b"thumbPosition")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.OutBack)

        self.update()

    def is_set(self) -> bool:
        return self._is_dark

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg_color = self._bg_dark if self._is_dark else self._bg_light
        corner_radius = self.height() / 2

        if self._show_border:
            p.setBrush(QBrush(Qt.GlobalColor.white))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(self.rect(), corner_radius, corner_radius)

            inner_rect = self.rect().adjusted(2, 2, -2, -2)
            p.setBrush(QBrush(bg_color))
            p.drawRoundedRect(inner_rect, corner_radius - 2.5, corner_radius - 2.5)
        else:
            p.setBrush(QBrush(bg_color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(self.rect(), corner_radius, corner_radius)

        thumb_diameter = self.height() - 6
        max_x = self.width() - thumb_diameter - 6
        thumb_x = 3 + int(self._thumb_pos * max_x)
        p.setBrush(QBrush(self._thumb_color))
        p.drawEllipse(thumb_x, 3, thumb_diameter, thumb_diameter)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()

    def toggle(self):
        self._is_dark = not self._is_dark
        self._animate_thumb()
        self.theme_changed.emit(self._is_dark)

    def set_state(self, state: bool, animate=True):
        if state != self._is_dark:
            self._is_dark = state
            if animate:
                self._animate_thumb()
            else:
                self._thumb_pos = 1.0 if state else 0.0
                self.update()

    def _animate_thumb(self):
        self._anim.stop()
        self._anim.setStartValue(self._thumb_pos)
        self._anim.setEndValue(1.0 if self._is_dark else 0.0)
        self._anim.start()

    def get_thumb_position(self) -> float:
        return self._thumb_pos

    def set_thumb_position(self, value: float) -> None:
        self._thumb_pos = value
        self.update()

    thumbPosition: float = Property(float, get_thumb_position, set_thumb_position)  # type:ignore
