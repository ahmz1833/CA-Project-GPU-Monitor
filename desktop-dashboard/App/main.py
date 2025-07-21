from PySide6.QtCore import QSize
from PySide6.QtWidgets import QMainWindow, QApplication
from qt_material import apply_stylesheet

import App.utils.Loader
from App.navigation.router import Router


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.router = Router.instance()
        self.setCentralWidget(self.router.stack)

        self.setMinimumSize(QSize(1024, 768))
        self.resize(1024, 768)

        self.router.navigate("welcome")


def main():
    app = QApplication([])
    font = App.utils.Loader.Loader().get_font()
    apply_stylesheet(
        app,
        theme='dark_blue.xml' if App.utils.Loader.Loader().is_dark() else 'light_pink.xml',
        extra={
            'density_scale': '0',
            'font_size': '13px',
            'font_family': f'{font.family()}'
        }
    )

    window = MainWindow()
    window.show()
    app.exec()
    # TODO: DELETE ALL THE PRINTS
