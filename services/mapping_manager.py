import json
import os
import sys
from pathlib import Path
from typing import Dict


def _default_mapping_file() -> Path:
    if getattr(sys, "frozen", False):
        local_app_data = os.getenv("LOCALAPPDATA")
        base_dir = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
        return base_dir / "DocFillPro" / "data" / "mappings.json"

    return Path(__file__).resolve().parent.parent / "data" / "mappings.json"


class MappingManager:
    """Gerencia marcadores adicionais salvos em JSON."""

    DEFAULT_FILE = _default_mapping_file()

    def __init__(self, file_path: str | Path | None = None) -> None:
        self.file_path = Path(file_path) if file_path else self.DEFAULT_FILE
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists() or not self.file_path.read_text(encoding="utf-8").strip():
            self.file_path.write_text("{}", encoding="utf-8")
        self._cache: Dict[str, str] | None = None

    def load(self) -> Dict[str, str]:
        if self._cache is not None:
            return dict(self._cache)

        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                cleaned: Dict[str, str] = {}
                for key, value in data.items():
                    try:
                        cleaned[self.normalize_marker(str(key))] = str(value).strip()
                    except ValueError:
                        continue
                self._cache = cleaned
                return dict(cleaned)
        except (OSError, json.JSONDecodeError):
            pass

        self._cache = {}
        return {}

    def save(self, mapping: Dict[str, str]) -> None:
        cleaned: Dict[str, str] = {}
        for key, value in mapping.items():
            try:
                cleaned[self.normalize_marker(str(key))] = str(value).strip()
            except ValueError:
                continue

        self.file_path.write_text(json.dumps(cleaned, indent=2, ensure_ascii=False), encoding="utf-8")
        self._cache = cleaned

    def add_marker(self, marker: str, value: str) -> Dict[str, str]:
        marker_text = self.normalize_marker(marker)
        data = self.load()
        data[marker_text] = value.strip()
        self.save(data)
        return data

    def build_replacements(self, base_values: Dict[str, str]) -> Dict[str, str]:
        replacements = self.load()
        for key, value in base_values.items():
            try:
                marker = self.normalize_marker(str(key))
            except ValueError:
                continue
            replacements[marker] = value if value is not None else ""
        return replacements

    @staticmethod
    def normalize_marker(marker: str) -> str:
        marker_text = marker.strip().upper()
        marker_text = marker_text.removeprefix("{{").removesuffix("}}").strip()
        marker_text = marker_text.strip("{}").strip()
        if not marker_text:
            raise ValueError("Informe um marcador válido.")
        return f"{{{{{marker_text}}}}}"
