import os
import sys

from PySide6.QtWidgets import QApplication

from App.pages.base_controller import BaseController


class Controller(BaseController):
    def __init__(self, view, router):
        super().__init__(view, router)

    def show_about(self):
        self.router.navigate("info", payload={'path': 'main.md', 'destination': 'home'})

    def show_gpu_info(self, gid):
        self.router.navigate("gpu", payload={'index': gid})

    @staticmethod
    def changeURL(text):
        if text.strip() == "":
            return
        QApplication.quit()
        script = os.path.abspath(sys.argv[0])
        new_argv = [sys.executable, script, text] + sys.argv[1:]
        os.execv(sys.executable, new_argv)
