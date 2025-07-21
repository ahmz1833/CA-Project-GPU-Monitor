from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QSlider, QHBoxLayout

from App.widgets.Label import Label


class Slider(QWidget):
    def __init__(self, label_text="", min_value=0, max_value=100,
                 value_type=float, initial_value=0, parent=None):
        super().__init__(parent)

        self.min_value = min_value
        self.max_value = max_value
        self.value_type = value_type
        self.internal_max = 10000

        self.label = Label(label_text)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.value_label = Label()

        self.slider.setRange(0, self.internal_max)
        self.slider.valueChanged.connect(self._update_value_label)

        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        layout.addWidget(self.value_label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.set_value(initial_value)

    def _update_value_label(self, internal_value):
        value = self._internal_to_value(internal_value)
        if self.value_type == float:
            self.value_label.setText(f"{value:.2f}")
        else:
            self.value_label.setText(f"{value}")

    def _value_to_internal(self, value):
        return int(((value - self.min_value) / (self.max_value - self.min_value)) * self.internal_max)

    def _internal_to_value(self, internal_value):
        ratio = internal_value / self.internal_max
        value = self.min_value + ratio * (self.max_value - self.min_value)

        if self.value_type == int:
            return int(round(value))
        return value

    def get_value(self):
        return self._internal_to_value(self.slider.value())

    def set_value(self, value):
        internal_value = self._value_to_internal(value)
        self.slider.setValue(internal_value)
        self._update_value_label(internal_value)
