from __future__ import annotations

from copy import deepcopy
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from services.runtime_paths import data_file, seed_file


class RuntimeJsonStore:
    """Pequeno store JSON com seed de bundle e escrita atomica."""

    filename = ""
    default_content: Any = {}

    def __init__(self, file_path: str | Path | None = None) -> None:
        self.file_path = Path(file_path) if file_path else data_file(self.filename)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache_data: dict[str, Any] | None = None
        self._cache_mtime_ns: int | None = None
        if not self.file_path.exists():
            self._initialize_storage()

    def load(self) -> dict[str, Any]:
        try:
            stat = self.file_path.stat()
            if self._cache_data is not None and self._cache_mtime_ns == stat.st_mtime_ns:
                return deepcopy(self._cache_data)
            raw_text = self.file_path.read_text(encoding="utf-8")
            if not raw_text.strip():
                payload = self._default_payload()
                self._remember_cache(payload, stat.st_mtime_ns)
                return deepcopy(payload)
            data = json.loads(raw_text)
            payload = data if isinstance(data, dict) else self._default_payload()
            self._remember_cache(payload, stat.st_mtime_ns)
            return deepcopy(payload)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            self._write_default()
            return deepcopy(self._default_payload())

    def save(self, data: dict[str, Any]) -> None:
        self._atomic_write(data)

    def _initialize_storage(self) -> None:
        seed = seed_file(self.filename)
        if seed.exists():
            try:
                content = seed.read_text(encoding="utf-8")
            except OSError:
                self._write_default()
                return
            if not content.strip():
                self._write_default()
                return
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                self._write_default()
                return
            self._atomic_write(parsed if isinstance(parsed, dict) else self._default_payload())
            return
        self._write_default()

    def _write_default(self) -> None:
        self._atomic_write(self._default_payload())

    def _default_payload(self) -> dict[str, Any]:
        if isinstance(self.default_content, dict):
            return dict(self.default_content)
        return {}

    def _atomic_write(self, data: dict[str, Any]) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.file_path.parent, delete=False) as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            temp_path = Path(handle.name)
        os.replace(temp_path, self.file_path)
        try:
            stat = self.file_path.stat()
            self._remember_cache(data, stat.st_mtime_ns)
        except OSError:
            self._remember_cache(data, None)

    def _remember_cache(self, data: dict[str, Any], mtime_ns: int | None) -> None:
        self._cache_data = deepcopy(data)
        self._cache_mtime_ns = mtime_ns
