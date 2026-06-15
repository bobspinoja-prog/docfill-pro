"""Load DocFill Pro internal symbol assets for UI contexts."""

from pathlib import Path
import sys

import customtkinter as ctk
from PIL import Image


class SymbolManager:
    """Loads the internal UI symbol without using it as the executable icon."""

    DEFAULT_SIZES = {
        "sidebar": 32,
        "header": 20,
        "empty": 96,
        "loading": 48,
    }

    _image_cache: dict[str, Image.Image] = {}

    @classmethod
    def get_symbol(cls, context: str = "sidebar", size: int | None = None) -> ctk.CTkImage | None:
        target_size = size or cls.DEFAULT_SIZES.get(context, 32)
        image = cls._load_image(context, target_size)
        if image is None:
            return None
        return ctk.CTkImage(image.copy(), size=(target_size, target_size))

    @classmethod
    def get_symbol_with_opacity(
        cls,
        context: str = "empty",
        opacity: float = 1.0,
        size: int | None = None,
    ) -> ctk.CTkImage | None:
        target_size = size or cls.DEFAULT_SIZES.get(context, 96)
        safe_opacity = max(0.0, min(1.0, opacity))
        cache_key = f"{context}:{target_size}:{safe_opacity:.2f}"
        if cache_key in cls._image_cache:
            image = cls._image_cache[cache_key].copy()
        else:
            image = cls._load_image(context, target_size)
            if image is None:
                return None
            if safe_opacity < 1.0:
                alpha = image.getchannel("A")
                alpha = alpha.point(lambda value: int(value * safe_opacity))
                image.putalpha(alpha)
            cls._image_cache[cache_key] = image.copy()
        return ctk.CTkImage(image, size=(target_size, target_size))

    @classmethod
    def clear_cache(cls) -> None:
        cls._image_cache.clear()

    @classmethod
    def _load_image(cls, context: str, target_size: int) -> Image.Image | None:
        asset_path = cls._find_symbol_path(context, target_size)
        if asset_path is None:
            return None

        try:
            image = Image.open(asset_path).convert("RGBA")
        except Exception as exc:
            print(f"Could not load symbol asset {asset_path}: {exc}")
            return None

        if image.size == (target_size, target_size):
            return image
        return cls._fit_square(image, target_size)

    @classmethod
    def _find_symbol_path(cls, context: str, target_size: int) -> Path | None:
        icons_dir = cls._icons_dir()
        candidates = [
            icons_dir / f"symbol_{context}_{target_size}x{target_size}.png",
            icons_dir / f"symbol_{context}.png",
            icons_dir / "symbol_original.png",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    @staticmethod
    def _fit_square(image: Image.Image, size: int) -> Image.Image:
        result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        source = image.copy()
        source.thumbnail((size, size), Image.Resampling.LANCZOS)
        x = (size - source.width) // 2
        y = (size - source.height) // 2
        result.alpha_composite(source, (x, y))
        return result

    @staticmethod
    def _icons_dir() -> Path:
        bundle_root = getattr(sys, "_MEIPASS", None)
        if bundle_root:
            return Path(bundle_root) / "assets" / "icons"
        return Path(__file__).resolve().parent.parent / "assets" / "icons"
