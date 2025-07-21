from App.pages.base_controller import BaseController


class Controller(BaseController):
    def __init__(self, view, router):
        super().__init__(view, router)
        self.index = 0
        self.real_name = ""

    def back(self):
        self.view.cleanup()
        self.router.navigate("home")

    def about(self):
        self.router.navigate("info", payload={'path': f'info.md', 'destination': 'env'})

    def reset(self):
        pass

    def on_navigate(self, payload: dict):
        self.index = payload['index']
        self.view._setup_ui()
        self.view.connect_buttons()
