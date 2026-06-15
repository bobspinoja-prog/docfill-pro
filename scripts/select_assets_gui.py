#!/usr/bin/env python3
"""Small GUI helper to copy visual assets into the project assets directory."""

import shutil
from pathlib import Path
from tkinter import Tk, filedialog, messagebox


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"


def _select_png(title: str) -> str:
    return filedialog.askopenfilename(
        title=title,
        filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
    )


def _copy_png(source: str, destination_name: str) -> Path:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    destination = ASSETS_DIR / destination_name
    shutil.copy2(source, destination)
    return destination


def select_and_save_assets() -> bool:
    root = Tk()
    root.withdraw()

    try:
        print("=" * 70)
        print("DocFill Pro - Asset Selection Helper")
        print("=" * 70)

        messagebox.showinfo(
            "External icon",
            "Select ICON_EXTERNAL.png.\n\n"
            "This is the app icon used by the window, executable, installer, and shortcuts.",
        )
        external_file = _select_png("Select ICON_EXTERNAL.png")
        if not external_file:
            messagebox.showerror("Canceled", "No file selected for the external icon.")
            return False

        external_dest = _copy_png(external_file, "ICON_EXTERNAL.png")
        print(f"[OK] Saved {external_dest}")
        messagebox.showinfo("Success", f"External icon saved to:\n{external_dest}")

        messagebox.showinfo(
            "Internal symbol",
            "Select SYMBOL_INTERNAL.png.\n\n"
            "This symbol is used inside the interface and is not the executable icon.",
        )
        internal_file = _select_png("Select SYMBOL_INTERNAL.png")
        if not internal_file:
            messagebox.showerror("Canceled", "No file selected for the internal symbol.")
            return False

        internal_dest = _copy_png(internal_file, "SYMBOL_INTERNAL.png")
        print(f"[OK] Saved {internal_dest}")
        messagebox.showinfo("Success", f"Internal symbol saved to:\n{internal_dest}")

        print("=" * 70)
        print("[OK] Both assets were saved.")
        print("Next step: python scripts/process_assets.py")
        print("=" * 70)
        return True
    finally:
        root.destroy()


if __name__ == "__main__":
    select_and_save_assets()
