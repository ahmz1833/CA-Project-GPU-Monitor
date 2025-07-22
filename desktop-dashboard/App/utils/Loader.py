import json
import pickle
from pathlib import Path
from typing import Any, Optional

import PySide6
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon, QPainter, QFontDatabase, QFont
from PySide6.QtSvg import QSvgRenderer


class Loader:
    _cache = {}
    _cache_max_size = 100
    _base_path = Path(__file__).parent.parent.parent / "assets"

    @classmethod
    def _get_full_path(cls, relative_path: str, folder_name: Optional[str] = None) -> Path:
        if folder_name is None:
            return cls._base_path / relative_path
        return cls._base_path / folder_name / relative_path

    @classmethod
    def _add_to_cache(cls, key: str, value: Any) -> None:
        if len(cls._cache) >= cls._cache_max_size:
            cls._cache.pop(next(iter(cls._cache)))
        cls._cache[key] = value

    @classmethod
    def _get_from_cache(cls, key: str) -> Any:
        return cls._cache.get(key)

    @classmethod
    def _remove_from_cache(cls, key: str) -> None:
        if key in cls._cache:
            cls._cache.pop(key)

    @classmethod
    def load_json(cls, path: str, is_temp: bool = False) -> dict:
        full_path = cls._get_full_path(path, "temp" if is_temp else "jsons")

        cache_key = f"json:{full_path}"
        if (cached := cls._get_from_cache(cache_key)) is not None:
            return cached

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            cls._add_to_cache(cache_key, data)
            return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to load JSON from {full_path}") from e

    @classmethod
    def load_image(cls, path: str, is_temp: bool = False) -> Image.Image:
        full_path = cls._get_full_path(path, "temp" if is_temp else "images")

        cache_key = f"image:{full_path}"
        if (cached := cls._get_from_cache(cache_key)) is not None:
            return cached

        try:
            image = Image.open(full_path)
            cls._add_to_cache(cache_key, image)
            return image
        except (FileNotFoundError, OSError) as e:
            raise ValueError(f"Failed to load image from {full_path}") from e

    @classmethod
    def load_pickle(cls, path: str, is_temp: bool = False) -> Any:
        full_path = cls._get_full_path(path, "temp" if is_temp else "pickles")

        cache_key = f"pickle:{full_path}"
        if (cached := cls._get_from_cache(cache_key)) is not None:
            return cached

        try:
            with open(full_path, 'rb') as f:
                data = pickle.load(f)
            cls._add_to_cache(cache_key, data)
            return data
        except (FileNotFoundError, pickle.PickleError) as e:
            raise ValueError(f"Failed to load pickle from {full_path}") from e

    @classmethod
    def load_bytes(cls, path: str, is_temp: bool = False) -> bytes:
        full_path = cls._get_full_path(path, "temp" if is_temp else "bytes")

        cache_key = f"bytes:{full_path}"
        if (cached := cls._get_from_cache(cache_key)) is not None:
            return cached
        try:
            with open(full_path, 'rb') as f:
                data = f.read()
            cls._add_to_cache(cache_key, data)
            return data
        except OSError as e:
            raise ValueError(f"Failed to load bytes from {full_path}") from e

    @classmethod
    def load_text(cls, path: str, is_temp: bool = False) -> str:
        return cls.load_bytes(path, is_temp).decode("utf-8")

    @classmethod
    def load_icon(cls, path: str, is_temp: bool = False) -> PySide6.QtGui.QIcon:

        full_path = cls._get_full_path("icons/" + path, "temp" if is_temp else "images")
        cache_key = f"icon:{full_path}"
        if (cached := cls._get_from_cache(cache_key)) is not None:
            return cached

        renderer = QSvgRenderer(f"{full_path}")
        if renderer.isValid():
            pixmap = QPixmap(renderer.defaultSize())
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            return QIcon(pixmap)

        return QIcon(f"{full_path}")

    @classmethod
    def is_dark(cls) -> bool:
        try:
            dic = cls.load_json("theme")
            if dic["theme"] == "light":
                return False
            elif dic["theme"] == "dark":
                return True
            else:
                cls.save_json("theme", {"theme": "dark"}, False)
                return True
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as _:
            cls.save_json("theme", {"theme": "dark"}, False)
            return True

    @classmethod
    def get_path(cls) -> Path:
        return Path(__file__).absolute().parent.parent.parent

    @classmethod
    def get_font(cls):
        full_path = cls._get_full_path("Comic Sans MS.ttf", "fonts")

        font_id = QFontDatabase.addApplicationFont(f"{full_path}")
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                custom_font = QFont(font_families[0])
                custom_font.setPointSize(13)
                return custom_font
        else:
            raise ValueError(f"Failed to load font from {full_path}")

    @classmethod
    def save_json(cls, path: str, data: dict, is_temp: bool, indent: int = 4) -> None:
        full_path = cls._get_full_path(path, "temp" if is_temp else "jsons")
        full_path.parent.mkdir(parents=True, exist_ok=True)

        cache_key = f"json:{full_path}"
        cls._remove_from_cache(cache_key)

        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent)
            cls._add_to_cache(cache_key, data)
        except (TypeError, OSError) as e:
            raise ValueError(f"Failed to save JSON to {full_path}") from e

    @classmethod
    def save_image(cls, path: str, image: Image.Image, is_temp: bool,
                   image_format: Optional[str] = None) -> None:
        full_path = cls._get_full_path(path, "temp" if is_temp else "images")
        full_path.parent.mkdir(parents=True, exist_ok=True)

        cache_key = f"image:{full_path}"
        cls._remove_from_cache(cache_key)

        try:
            image.save(full_path, format=image_format)
            cls._add_to_cache(cache_key, image)
        except (ValueError, OSError) as e:
            raise ValueError(f"Failed to save image to {full_path}") from e

    @classmethod
    def save_pickle(cls, path: str, obj: Any, is_temp: bool) -> None:
        full_path = cls._get_full_path(path, "temp" if is_temp else "pickles")
        full_path.parent.mkdir(parents=True, exist_ok=True)

        cache_key = f"pickle:{full_path}"
        cls._remove_from_cache(cache_key)

        try:
            with open(full_path, 'wb') as f:
                pickle.dump(obj, f)
            cls._add_to_cache(cache_key, obj)
        except (pickle.PickleError, OSError) as e:
            raise ValueError(f"Failed to save pickle to {full_path}") from e

    @classmethod
    def save_bytes(cls, path: str, data, is_temp: bool) -> None:
        full_path = cls._get_full_path(path, "temp" if is_temp else "bytes")
        full_path.parent.mkdir(parents=True, exist_ok=True)

        cache_key = f"bytes:{full_path}"
        cls._remove_from_cache(cache_key)

        try:
            with open(full_path, 'wb') as f:
                f.write(data)
            cls._add_to_cache(cache_key, data)
        except OSError as e:
            raise ValueError(f"Failed to save bytes to {full_path}") from e

    @classmethod
    def save_text(cls, path: str, data: str, is_temp: bool) -> None:
        cls.save_bytes(path, data.encode('utf-8'), is_temp)

    @classmethod
    def destroy_instance(cls):
        cls._cache = {}
