from typing import Union, Literal

from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (QHBoxLayout, QLineEdit)

from App.widgets.Label import Label


class SingleInput(QHBoxLayout):

    def __init__(self,
                 label: str = "",
                 parent=None,
                 input_type: Literal['float', 'int', 'text'] = 'float'):
        super().__init__(parent)
        self.input_field = None
        self.input_type = input_type
        self.setup_ui(label)

    def setup_ui(self, label: str):
        self.setContentsMargins(0, 0, 0, 0)

        if label:
            self.addWidget(Label(label))

        self.input_field = self._create_input_field()
        self.addWidget(self.input_field)

    def _create_input_field(self) -> QLineEdit:
        input_field = QLineEdit()

        if self.input_type == 'float':
            validator = QDoubleValidator()
            validator.setNotation(QDoubleValidator.Notation.ScientificNotation)
            input_field.setValidator(validator)
        elif self.input_type == 'int':
            input_field.setValidator(QIntValidator())

        return input_field

    def get_value(self) -> Union[float, int, str]:
        text = self.input_field.text()

        if self.input_type == 'float':
            try:
                return float(text)
            except ValueError as e:
                raise e
        elif self.input_type == 'int':
            try:
                return int(text)
            except ValueError as e:
                raise e
        else:
            return text

    def set_value(self, value: Union[float, int, str]):
        if self.input_type == 'float':
            if not isinstance(value, (float, int)):
                raise ValueError("Float input requires numeric value")
        elif self.input_type == 'int':
            if not isinstance(value, int):
                raise ValueError("Integer input requires integer value")

        self.input_field.setText(str(value))

    def clear(self):
        self.input_field.clear()
