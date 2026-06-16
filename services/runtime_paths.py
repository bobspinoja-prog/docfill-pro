from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "DocFillPro"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resource_root() -> Path:
    if getattr(sys, "frozen", False):
        bundle_root = getattr(sys, "_MEIPASS", None)
        if bundle_root:
            return Path(bundle_root)
    return repo_root()


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        local_app_data = os.getenv("LOCALAPPDATA")
        base_dir = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
        return base_dir / APP_NAME
    return repo_root()


def data_dir() -> Path:
    return app_root() / "data"


def log_dir() -> Path:
    return app_root() / "logs"


def data_file(name: str) -> Path:
    return data_dir() / name


def seed_file(name: str) -> Path:
    return resource_root() / "data" / name
