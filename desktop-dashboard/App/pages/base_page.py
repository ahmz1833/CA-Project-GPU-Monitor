from PySide6.QtWidgets import QWidget


class BasePage(QWidget):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.controller = None

    def set_controller(self, controller):
        self.controller = controller

    def _setup_ui(self):
        raise NotImplementedError

    def connect_signals(self):
        pass
