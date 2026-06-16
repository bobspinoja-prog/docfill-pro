from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from services.runtime_json_store import RuntimeJsonStore


class UserSettingsStore(RuntimeJsonStore):
    filename = "user_settings.json"
    default_content = {
        "recent_templates": [],
        "recent_exports": [],
        "last_template_path": "",
        "last_template_name": "",
        "last_template_hash": "",
        "last_output_folder": "",
        "last_values": {},
        "autosave": None,
    }

    def set_last_template(
        self,
        template_path: str | Path,
        template_name: str,
        template_hash: str,
        values: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        data = self.load()
        normalized_path = str(Path(template_path))
        self._push_recent(
            data,
            {
                "path": normalized_path,
                "name": template_name,
                "hash": template_hash,
                "seen_at": self._now(),
            },
            list_key="recent_templates",
            unique_key="hash",
        )
        data["last_template_path"] = normalized_path
        data["last_template_name"] = template_name
        data["last_template_hash"] = template_hash
        if values is not None:
            data["last_values"] = dict(values)
        data["updated_at"] = self._now()
        self.save(data)
        return data

    def set_last_output_folder(self, output_folder: str | Path) -> dict[str, Any]:
        data = self.load()
        data["last_output_folder"] = str(Path(output_folder))
        data["updated_at"] = self._now()
        self.save(data)
        return data

    def save_autosave(
        self,
        template_path: str | Path | None,
        template_name: str,
        template_hash: str | None,
        output_folder: str | Path | None,
        values: dict[str, str],
        markers: list[str] | None = None,
    ) -> dict[str, Any]:
        data = self.load()
        data["autosave"] = {
            "template_path": str(template_path) if template_path else "",
            "template_name": template_name,
            "template_hash": template_hash or "",
            "output_folder": str(output_folder) if output_folder else "",
            "values": dict(values),
            "markers": list(markers or []),
            "updated_at": self._now(),
        }
        data["last_values"] = dict(values)
        data["updated_at"] = self._now()
        self.save(data)
        return data

    def clear_autosave(self) -> dict[str, Any]:
        data = self.load()
        data["autosave"] = None
        data["updated_at"] = self._now()
        self.save(data)
        return data

    def load_autosave(self) -> dict[str, Any] | None:
        autosave = self.load().get("autosave")
        return dict(autosave) if isinstance(autosave, dict) else None

    def record_export(
        self,
        template_hash: str,
        template_name: str,
        output_path: str | Path,
    ) -> dict[str, Any]:
        data = self.load()
        self._push_recent(
            data,
            {
                "template_hash": template_hash,
                "template_name": template_name,
                "output_path": str(Path(output_path)),
                "exported_at": self._now(),
            },
            list_key="recent_exports",
            unique_key="output_path",
        )
        data["updated_at"] = self._now()
        self.save(data)
        return data

    def get_recent_templates(self, limit: int = 5) -> list[dict[str, Any]]:
        data = self.load()
        templates = data.get("recent_templates", [])
        return [dict(item) for item in templates[:limit] if isinstance(item, dict)]

    def get_recent_exports(self, limit: int = 5) -> list[dict[str, Any]]:
        data = self.load()
        exports = data.get("recent_exports", [])
        return [dict(item) for item in exports[:limit] if isinstance(item, dict)]

    def _push_recent(
        self,
        data: dict[str, Any],
        item: dict[str, Any],
        *,
        list_key: str,
        unique_key: str,
        limit: int = 10,
    ) -> None:
        entries = [dict(entry) for entry in data.get(list_key, []) if isinstance(entry, dict)]
        key_value = item.get(unique_key)
        entries = [entry for entry in entries if entry.get(unique_key) != key_value]
        entries.insert(0, item)
        data[list_key] = entries[:limit]

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")
