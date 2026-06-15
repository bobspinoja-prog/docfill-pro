#!/usr/bin/env python3
"""
Process visual assets for DocFill Pro.

Expected input files:
- assets/ICON_EXTERNAL.png
- assets/SYMBOL_INTERNAL.png
"""

from pathlib import Path
import sys

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
ICONS_DIR = ASSETS_DIR / "icons"

ICO_SIZES = [16, 24, 32, 48, 64, 128, 256, 512]
ICO_EMBED_SIZES = [16, 24, 32, 48, 64, 128, 256]


def _fit_square(image: Image.Image, size: int) -> Image.Image:
    """Center-crop to square and resize for icon contexts."""
    source = image.copy()
    side = min(source.width, source.height)
    left = (source.width - side) // 2
    top = (source.height - side) // 2
    source = source.crop((left, top, left + side, top + side))
    return source.resize((size, size), Image.Resampling.LANCZOS)


def process_external_icon() -> bool:
    source = ASSETS_DIR / "ICON_EXTERNAL.png"

    if not source.exists():
        print(f"[MISSING] {source}")
        print("Place ICON_EXTERNAL.png in the project assets/ directory.")
        return False

    ICONS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        image = Image.open(source).convert("RGBA")
        print(f"[OK] Loaded {source.name} ({image.width}x{image.height})")

        versions = {}
        for size in ICO_SIZES:
            resized = _fit_square(image, size)
            versions[size] = resized
            png_path = ICONS_DIR / f"docfill_{size}x{size}.png"
            resized.save(png_path, "PNG")
            print(f"  [OK] Created {png_path.relative_to(PROJECT_ROOT)}")

        ico_path = ICONS_DIR / "docfill.ico"
        versions[512].save(
            ico_path,
            "ICO",
            sizes=[(size, size) for size in ICO_EMBED_SIZES],
        )
        print(f"[OK] Created {ico_path.relative_to(PROJECT_ROOT)}")

        app_icon_path = ASSETS_DIR / "app_icon.ico"
        versions[512].save(
            app_icon_path,
            "ICO",
            sizes=[(size, size) for size in ICO_EMBED_SIZES],
        )
        print(f"[OK] Updated {app_icon_path.relative_to(PROJECT_ROOT)}")
        return True
    except Exception as exc:
        print(f"[ERROR] Could not process {source.name}: {exc}")
        return False


def process_internal_symbol() -> bool:
    source = ASSETS_DIR / "SYMBOL_INTERNAL.png"

    if not source.exists():
        print(f"[MISSING] {source}")
        print("Place SYMBOL_INTERNAL.png in the project assets/ directory.")
        return False

    ICONS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        image = Image.open(source).convert("RGBA")
        print(f"[OK] Loaded {source.name} ({image.width}x{image.height})")

        symbol_sizes = {
            "sidebar": 32,
            "header": 20,
            "empty": 96,
            "loading": 48,
        }

        for context, size in symbol_sizes.items():
            resized = _fit_square(image, size)
            path = ICONS_DIR / f"symbol_{context}_{size}x{size}.png"
            resized.save(path, "PNG")
            print(f"  [OK] Created {path.relative_to(PROJECT_ROOT)}")

        original_path = ICONS_DIR / "symbol_original.png"
        image.save(original_path, "PNG")
        print(f"  [OK] Saved {original_path.relative_to(PROJECT_ROOT)}")
        return True
    except Exception as exc:
        print(f"[ERROR] Could not process {source.name}: {exc}")
        return False


def main() -> int:
    print("=" * 60)
    print("DocFill Pro - Asset Integration Tool")
    print("=" * 60)

    external_ok = process_external_icon()
    internal_ok = process_internal_symbol()

    print("=" * 60)
    if external_ok and internal_ok:
        print("[OK] Asset integration completed.")
        return 0

    print("[WARN] Some source assets are still missing.")
    print("Save the PNG files in assets/ and run this script again.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
