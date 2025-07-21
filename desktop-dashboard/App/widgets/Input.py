from typing import Union, Literal, Tuple

from PySide6.QtCore import Signal
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import QHBoxLayout, QLineEdit

from App.widgets.Label import Label


class BaseInput(QHBoxLayout):
    def __init__(self,
                 label: str = "",
                 parent=None,
                 input_type: Literal['float', 'int', 'text'] = 'float'):
        super().__init__(parent)
        self.input_type = input_type
        self.setup_ui(label)

    def setup_ui(self, label: str):
        self.setContentsMargins(0, 0, 0, 0)
        if label:
            self.addWidget(Label(label))

    def _create_input_field(self) -> QLineEdit:
        input_field = QLineEdit()

        if self.input_type == 'float':
            validator = QDoubleValidator()
            validator.setNotation(QDoubleValidator.Notation.ScientificNotation)
            input_field.setValidator(validator)
        elif self.input_type == 'int':
            input_field.setValidator(QIntValidator())

        return input_field

    def _convert_value(self, text: str) -> Union[float, int, str]:
        if not text:
            return self._get_default_value()

        if self.input_type == 'float':
            return float(text)
        elif self.input_type == 'int':
            return int(text)
        return text

    def _get_default_value(self):
        if self.input_type == 'float':
            return 0.0
        elif self.input_type == 'int':
            return 0
        return ""

    def _validate_value(self, value: Union[float, int, str]):
        if self.input_type == 'float' and not isinstance(value, (float, int)):
            raise ValueError("Float input requires numeric value")
        elif self.input_type == 'int' and not isinstance(value, int):
            raise ValueError("Integer input requires integer value")

    def clear(self):
        for i in range(self.count()):
            widget = self.itemAt(i).widget()
            if isinstance(widget, QLineEdit):
                widget.clear()


class SingleInput(BaseInput):
    valueChanged = Signal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_field = None

    def setup_ui(self, label: str):
        super().setup_ui(label)
        self.input_field = self._create_input_field()
        self.addWidget(self.input_field)
        self.input_field.textChanged.connect(self._emit_value_changed)

    def _emit_value_changed(self):
        value = self.get_value()
        self.valueChanged.emit(value)

    def get_value(self) -> Union[float, int, str]:
        try:
            return self._convert_value(self.input_field.text())
        except ValueError as e:
            raise e

    def set_value(self, value: Union[float, int, str]):
        self._validate_value(value)
        self.input_field.setText(str(value))


class RangeInput(BaseInput):
    rangeChanged = Signal(object, object)

    def __init__(self, *args, **kwargs):
        self.start_input = None
        self.end_input = None
        super().__init__(*args, **kwargs)

    def setup_ui(self, label: str):
        super().setup_ui(label)

        self.start_input = self._create_input_field()
        self.addWidget(self.start_input)

        self.addWidget(Label("to"))

        self.end_input = self._create_input_field()
        self.addWidget(self.end_input)

        self.start_input.textChanged.connect(self._emit_range_changed)
        self.end_input.textChanged.connect(self._emit_range_changed)

    def _emit_range_changed(self):
        try:
            start, end = self.get_range()
            self.rangeChanged.emit(start, end)
        except ValueError:
            pass

    def get_range(self) -> Tuple[Union[float, int, str], Union[float, int, str]]:
        if self.start_input is None or self.end_input is None:
            return self._get_default_value(), self._get_default_value()

        try:
            start = self._convert_value(self.start_input.text())
            end = self._convert_value(self.end_input.text())
            return start, end
        except ValueError as e:
            raise e

    def set_range(self, start: Union[float, int, str], end: Union[float, int, str]):
        self._validate_value(start)
        self._validate_value(end)
        if self.start_input is not None:
            self.start_input.setText(str(start))
        if self.end_input is not None:
            self.end_input.setText(str(end))
