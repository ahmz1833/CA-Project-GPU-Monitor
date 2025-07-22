from collections import OrderedDict
from threading import Lock
from typing import Optional, Dict, Protocol, runtime_checkable

from PySide6.QtWidgets import QStackedWidget, QWidget, QApplication

from App.navigation.pages import PAGE_REGISTRY, get_icon


@runtime_checkable
class Navigable(Protocol):
    def on_navigate(self, payload: dict) -> None: ...


class _RouterMeta(type):
    _instances: Dict[type, 'Router'] = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class Router(metaclass=_RouterMeta):
    def __init__(self, max_cache_size: int = 1):
        if not hasattr(self, '_initialized'):
            self.stack: QStackedWidget = QStackedWidget()
            self._page_cache: OrderedDict[str, QWidget] = OrderedDict()
            self.max_cache_size: int = max_cache_size
            self._lock: Lock = Lock()
            self._initialized: bool = True

    @classmethod
    def instance(cls) -> 'Router':
        return cls()

    def navigate(self, page_name: str, payload: Optional[dict] = None) -> None:
        if page_name not in PAGE_REGISTRY:
            raise ValueError(f"Unknown page: {page_name}")

        with self._lock:
            page = self._get_or_create_page(page_name)
            self._update_cache(page_name, page)

        try:
            if hasattr(page, 'controller') and page.controller:
                if hasattr(page.controller, 'initialize'):
                    page.controller.initialize()

                if payload is not None:
                    if hasattr(page.controller, 'on_navigate'):
                        page.controller.on_navigate(payload)
        except Exception as e:
            raise Exception(f"Controller initialization error: {e}")

        self._update_window_properties(page_name)
        self.stack.setCurrentWidget(page)

    def _update_window_properties(self, page_name: str) -> None:
        main_window = self.stack.window()
        if not main_window:
            main_window = QApplication.activeWindow()
            if not main_window:
                return

        try:
            page_info = PAGE_REGISTRY[page_name]
            title = page_info.get('title', page_name)
            main_window.setWindowTitle(title)
            icon = get_icon(page_name)
            if not icon.isNull():
                main_window.setWindowIcon(icon)
        except Exception as e:
            raise Exception(f"Error updating window properties: {e}")

    def _get_or_create_page(self, page_name: str) -> QWidget:
        if page := self._page_cache.get(page_name):
            self._page_cache.move_to_end(page_name)
            return page
        return self._load_page(page_name)

    def _load_page(self, page_name: str) -> QWidget:
        try:
            page_info = PAGE_REGISTRY[page_name]
            module = __import__(
                f"App.pages.{page_info['module']}.view",
                fromlist=["View"]
            )
            page = module.View(self)
            self.stack.addWidget(page)
            return page
        except ImportError as e:
            raise ImportError(f"Page import failed: {page_name} - {e}")
        except Exception as e:
            raise RuntimeError(f"Page creation failed: {page_name} - {e}")

    def _update_cache(self, page_name: str, page: QWidget) -> None:
        if page_name not in self._page_cache:
            if len(self._page_cache) >= self.max_cache_size:
                self._evict_oldest_page()
            self._page_cache[page_name] = page
        self._page_cache.move_to_end(page_name)

    def _evict_oldest_page(self) -> None:
        oldest_name, oldest_page = self._page_cache.popitem(last=False)
        self.stack.removeWidget(oldest_page)
        oldest_page.deleteLater()

    @classmethod
    def destroy_instance(cls) -> None:
        if cls in cls._instances:
            router = cls._instances.pop(cls)
            for page in router._page_cache.values():
                page.deleteLater()
            router._page_cache.clear()
            router.stack.deleteLater()

    @classmethod
    def clear_instance(cls) -> None:
        cls.instance().stack = QStackedWidget()
        cls.instance()._page_cache = OrderedDict()
