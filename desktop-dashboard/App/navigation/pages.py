from PySide6.QtGui import QIcon

import App.utils.Loader as Ld

PAGE_REGISTRY = {
    "home": {
        "module": "home",
        "title": "Home",
        "icon": "main.png",
    },
    "welcome": {
        "module": "welcome",
        "title": "GPU Monitor",
        "icon": "main.png",
    },
    "info": {
        "module": "markdown",
        "title": "information",
        "icon": "main.png",
    },
    "gpu": {
        "module": "gpu",
        "title": "GPU Info",
        "icon": "main.png",
    },
}


def get_icon(page_name: str) -> QIcon:
    ld = Ld.Loader()
    if page_name not in PAGE_REGISTRY:
        return QIcon()
    icon_file = PAGE_REGISTRY[page_name].get("icon", "")
    return ld.load_icon(icon_file) if icon_file else QIcon()
