from App.pages.base_controller import BaseController


class Controller(BaseController):
    def __init__(self, view, router):
        super().__init__(view, router)

    def skip_welcome(self):
        self.router.navigate("home")
