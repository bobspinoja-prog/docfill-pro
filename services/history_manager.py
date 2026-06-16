from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from services.runtime_json_store import RuntimeJsonStore


class HistoryManager(RuntimeJsonStore):
    filename = "history.json"
    default_content = {"records": []}

    def record_document(
        self,
        *,
        template_name: str,
        template_hash: str,
        output_file: str | Path,
        document_name: str,
        fields: dict[str, str],
        detected_fields: dict[str, dict[str, Any]] | None = None,
        profile_used: str | None = None,
        template_path: str | Path | None = None,
        output_folder: str | Path | None = None,
        favorite: bool = False,
    ) -> dict[str, Any]:
        data = self.load()
        records = self._records(data)
        entry = {
            "id": uuid.uuid4().hex,
            "timestamp": self._now(),
            "template_name": template_name,
            "template_hash": template_hash,
            "template_path": str(template_path) if template_path else "",
            "output_file": str(Path(output_file)),
            "output_folder": str(output_folder) if output_folder else "",
            "document_name": document_name,
            "fields": dict(fields),
            "detected_fields": dict(detected_fields or {}),
            "profile_used": profile_used or "",
            "favorite": bool(favorite),
        }
        records.insert(0, entry)
        data["records"] = records[:500]
        self.save(data)
        return entry

    def query_records(
        self,
        *,
        search: str = "",
        template_name: str = "",
        date_from: str = "",
        date_to: str = "",
        favorites_only: bool = False,
    ) -> list[dict[str, Any]]:
        search_text = search.strip().lower()
        template_filter = template_name.strip().lower()
        start = self._parse_date(date_from)
        end = self._parse_date(date_to, end_of_day=True)
        matches: list[dict[str, Any]] = []
        for record in self._records(self.load()):
            if favorites_only and not record.get("favorite"):
                continue
            if template_filter and template_filter not in str(record.get("template_name", "")).lower():
                continue
            if search_text and not self._record_matches(record, search_text):
                continue
            timestamp = self._parse_datetime(record.get("timestamp", ""))
            if start and timestamp and timestamp < start:
                continue
            if end and timestamp and timestamp > end:
                continue
            matches.append(dict(record))
        return matches

    def get_record(self, record_id: str) -> dict[str, Any] | None:
        for record in self._records(self.load()):
            if record.get("id") == record_id:
                return dict(record)
        return None

    def set_favorite(self, record_id: str, favorite: bool = True) -> dict[str, Any] | None:
        data = self.load()
        records = self._records(data)
        changed = None
        for record in records:
            if record.get("id") == record_id:
                record["favorite"] = bool(favorite)
                record["updated_at"] = self._now()
                changed = dict(record)
                break
        if changed is not None:
            data["records"] = records
            self.save(data)
        return changed

    def recent_templates(self, limit: int = 10) -> list[dict[str, Any]]:
        seen: set[str] = set()
        templates: list[dict[str, Any]] = []
        for record in self._records(self.load()):
            key = str(record.get("template_hash", ""))
            if not key or key in seen:
                continue
            seen.add(key)
            templates.append(
                {
                    "template_hash": key,
                    "template_name": record.get("template_name", ""),
                    "template_path": record.get("template_path", ""),
                    "last_used_at": record.get("timestamp", ""),
                }
            )
            if len(templates) >= limit:
                break
        return templates

    def recent_documents(self, limit: int = 10) -> list[dict[str, Any]]:
        return [dict(record) for record in self._records(self.load())[:limit]]

    def _records(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        records = data.get("records", [])
        return [dict(item) for item in records if isinstance(item, dict)]

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def _record_matches(record: dict[str, Any], search_text: str) -> bool:
        haystack = " ".join(
            str(record.get(key, ""))
            for key in ("template_name", "document_name", "output_file", "template_hash")
        ).lower()
        if search_text in haystack:
            return True
        fields = record.get("fields", {})
        if isinstance(fields, dict):
            field_text = " ".join(str(value) for value in fields.values()).lower()
            if search_text in field_text:
                return True
        detected = record.get("detected_fields", {})
        if isinstance(detected, dict):
            detected_text = " ".join(str(value) for value in detected.values()).lower()
            if search_text in detected_text:
                return True
        return False

    @staticmethod
    def _parse_datetime(value: str):
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            try:
                return datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                return None

    def _parse_date(self, value: str, end_of_day: bool = False):
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            try:
                parsed = datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                return None
        if end_of_day:
            return parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
        return parsed.replace(hour=0, minute=0, second=0, microsecond=0)
