from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from services.runtime_json_store import RuntimeJsonStore


class UserSessionStore(RuntimeJsonStore):
    filename = "user_session.json"
    default_content = {
        "autosave": None,
        "recent_templates": [],
        "recent_documents": [],
        "last_template_path": "",
        "last_template_name": "",
        "last_template_hash": "",
        "last_output_folder": "",
        "last_values": {},
        "active_view": "main",
    }

    def save_autosave(
        self,
        template_path: str | Path | None,
        template_name: str,
        template_hash: str | None,
        output_folder: str | Path | None,
        values: dict[str, str],
        current_view: str = "main",
        detected_fields: dict[str, Any] | None = None,
        pdf_area_mappings: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = self.load()
        data["autosave"] = {
            "template_path": str(template_path) if template_path else "",
            "template_name": template_name,
            "template_hash": template_hash or "",
            "output_folder": str(output_folder) if output_folder else "",
            "values": dict(values),
            "detected_fields": dict(detected_fields or {}),
            "pdf_area_mappings": dict(pdf_area_mappings or {}),
            "current_view": current_view,
            "updated_at": self._now(),
        }
        data["last_template_path"] = str(template_path) if template_path else ""
        data["last_template_name"] = template_name
        data["last_template_hash"] = template_hash or ""
        data["last_output_folder"] = str(output_folder) if output_folder else ""
        data["last_values"] = dict(values)
        data["active_view"] = current_view
        data["updated_at"] = self._now()
        self._atomic_write(data)
        return data

    def set_last_template(
        self,
        template_path: str | Path,
        template_name: str,
        template_hash: str,
        values: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        data = self.load()
        data["last_template_path"] = str(Path(template_path))
        data["last_template_name"] = template_name
        data["last_template_hash"] = template_hash
        if values is not None:
            data["last_values"] = dict(values)
        data["updated_at"] = self._now()
        recent = self._push_recent(
            data.get("recent_templates", []),
            {
                "template_path": str(Path(template_path)),
                "template_name": template_name,
                "template_hash": template_hash,
                "updated_at": self._now(),
            },
            "template_hash",
        )
        data["recent_templates"] = recent
        self._atomic_write(data)
        return data

    def set_last_output_folder(self, output_folder: str | Path) -> dict[str, Any]:
        data = self.load()
        data["last_output_folder"] = str(Path(output_folder))
        data["updated_at"] = self._now()
        self._atomic_write(data)
        return data

    def load_autosave(self) -> dict[str, Any] | None:
        autosave = self.load().get("autosave")
        return dict(autosave) if isinstance(autosave, dict) else None

    def clear_autosave(self) -> dict[str, Any]:
        data = self.load()
        data["autosave"] = None
        data["updated_at"] = self._now()
        self._atomic_write(data)
        return data

    def record_recent_template(
        self,
        template_path: str | Path,
        template_name: str,
        template_hash: str,
    ) -> dict[str, Any]:
        data = self.load()
        recent = self._push_recent(
            data.get("recent_templates", []),
            {
                "template_path": str(template_path),
                "template_name": template_name,
                "template_hash": template_hash,
                "updated_at": self._now(),
            },
            "template_hash",
        )
        data["recent_templates"] = recent
        data["updated_at"] = self._now()
        self._atomic_write(data)
        return data

    def record_recent_document(
        self,
        *,
        document_name: str,
        template_name: str,
        output_file: str | Path,
        output_folder: str | Path | None = None,
    ) -> dict[str, Any]:
        data = self.load()
        recent = self._push_recent(
            data.get("recent_documents", []),
            {
                "document_name": document_name,
                "template_name": template_name,
                "output_file": str(output_file),
                "output_folder": str(output_folder) if output_folder else "",
                "updated_at": self._now(),
            },
            "output_file",
        )
        data["recent_documents"] = recent
        data["updated_at"] = self._now()
        self._atomic_write(data)
        return data

    def record_export(
        self,
        template_hash: str,
        template_name: str,
        output_path: str | Path,
    ) -> dict[str, Any]:
        return self.record_recent_document(
            document_name=Path(output_path).name,
            template_name=template_name,
            output_file=output_path,
            output_folder=Path(output_path).parent,
        )

    def recent_templates(self, limit: int = 10) -> list[dict[str, Any]]:
        return [dict(item) for item in self.load().get("recent_templates", [])[:limit] if isinstance(item, dict)]

    def recent_documents(self, limit: int = 10) -> list[dict[str, Any]]:
        return [dict(item) for item in self.load().get("recent_documents", [])[:limit] if isinstance(item, dict)]

    def _push_recent(self, items: list[dict[str, Any]], item: dict[str, Any], unique_key: str, limit: int = 10) -> list[dict[str, Any]]:
        entries = [dict(entry) for entry in items if isinstance(entry, dict)]
        entries = [entry for entry in entries if entry.get(unique_key) != item.get(unique_key)]
        entries.insert(0, item)
        return entries[:limit]

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")
