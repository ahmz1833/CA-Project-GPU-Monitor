from App.pages.base_controller import BaseController


class Controller(BaseController):
    def __init__(self, view, router):
        super().__init__(view, router)
        self.path = None
        self.destination = None

    def navigate_to_page2(self):
        self.router.navigate(self.destination)

    def on_navigate(self, payload: dict):
        self.path = payload["path"]
        self.destination = payload["destination"]
        self.view._setup_ui()

    def initialize(self):
        pass
