class BaseController:
    def __init__(self, view, router):
        self.view = view
        self.router = router

    def initialize(self):
        pass

    def on_navigate(self, payload: dict):
        pass

    def finish_navigation(self):
        pass
