from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from services.runtime_paths import log_dir


class StructuredLogger:
    """Escreve eventos em JSONL para diagnostico simples."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else log_dir()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, level: str = "info", message: str = "", **payload: Any) -> Path:
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "level": level,
            "event": event,
            "message": message,
            **payload,
        }
        file_path = self.base_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with file_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return file_path
