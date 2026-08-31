from __future__ import annotations

from typing import Dict

from services.runtime_json_store import RuntimeJsonStore


class MappingManager(RuntimeJsonStore):
    """Gerencia marcadores adicionais salvos em JSON."""

    filename = "mappings.json"
    default_content: Dict[str, str] = {}

    def load(self) -> Dict[str, str]:
        raw = super().load()
        cleaned: Dict[str, str] = {}
        for key, value in raw.items():
            try:
                cleaned[self.normalize_marker(str(key))] = str(value).strip()
            except ValueError:
                continue
        return cleaned

    def save(self, mapping: Dict[str, str]) -> None:
        cleaned: Dict[str, str] = {}
        for key, value in mapping.items():
            try:
                cleaned[self.normalize_marker(str(key))] = str(value).strip()
            except ValueError:
                continue
        super().save(cleaned)

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
