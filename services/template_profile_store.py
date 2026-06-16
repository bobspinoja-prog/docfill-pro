from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from services.runtime_json_store import RuntimeJsonStore
from services.template_semantic_analyzer import FIELD_LABELS, SemanticDetection


FIELD_GROUPS = {
    "{{COMPRADOR}}": "Dados do Comprador",
    "{{NACIONALIDADE}}": "Dados do Comprador",
    "{{PROFISSAO}}": "Dados do Comprador",
    "{{ESTADO_CIVIL}}": "Dados do Comprador",
    "{{CPF_CNPJ}}": "Dados do Comprador",
    "{{LOTE}}": "Dados do Imóvel",
    "{{QUADRA}}": "Dados do Imóvel",
    "{{EMPREENDIMENTO}}": "Dados do Imóvel",
    "{{VENDEDOR}}": "Dados do Vendedor",
    "{{CIDADE}}": "Dados do Documento",
    "{{DATA}}": "Dados do Documento",
}


class TemplateProfileStore(RuntimeJsonStore):
    filename = "template_profiles.json"
    default_content = {}

    def load_profile(self, template_hash: str) -> dict[str, Any]:
        data = self.load()
        profile = data.get(template_hash, {})
        return dict(profile) if isinstance(profile, dict) else {}

    def update_profile(
        self,
        template_hash: str,
        template_name: str,
        detections: dict[str, SemanticDetection] | None = None,
        placeholders: list[str] | None = None,
        required_fields: set[str] | None = None,
        manual_values: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        data = self.load()
        profile = dict(data.get(template_hash, {}) if isinstance(data.get(template_hash, {}), dict) else {})
        detections = detections or {}
        placeholders = placeholders or []
        required_fields = required_fields or set()
        manual_values = manual_values or {}

        previous_history = [dict(item) for item in profile.get("history", []) if isinstance(item, dict)]
        previous_corrections = [dict(item) for item in profile.get("corrections", []) if isinstance(item, dict)]

        field_values = {
            field: detection.value
            for field, detection in detections.items()
            if detection.value
        }
        learned_fields = sorted(set(profile.get("learned_fields", [])) | set(field_values) | {field for field, value in manual_values.items() if value})

        profile.update(
            {
                "hash": template_hash,
                "template_name": template_name,
                "updated_at": self._now(),
                "last_used_at": self._now(),
                "usage_count": int(profile.get("usage_count", 0)) + 1,
                "placeholders": list(dict.fromkeys(placeholders)),
                "required_fields": sorted(required_fields),
                "learned_fields": learned_fields,
                "fields_found": learned_fields,
                "labels": {field: FIELD_LABELS.get(field, field) for field in learned_fields},
                "groups": {field: FIELD_GROUPS.get(field, "Dados do Documento") for field in learned_fields},
                "manual_values": {field: value for field, value in manual_values.items() if value},
                "field_values": field_values,
                "history": previous_history,
                "corrections": previous_corrections,
            }
        )
        profile["history"].append(
            {
                "at": self._now(),
                "event": "template_loaded",
                "template_name": template_name,
                "fields_detected": len(field_values),
                "placeholders": len(placeholders),
            }
        )
        data[template_hash] = profile
        self.save(data)
        return profile

    def record_correction(
        self,
        template_hash: str,
        template_name: str,
        detection: SemanticDetection,
        action: str = "manual_correction",
    ) -> dict[str, Any]:
        data = self.load()
        profile = dict(data.get(template_hash, {}) if isinstance(data.get(template_hash, {}), dict) else {})
        corrections = [dict(item) for item in profile.get("corrections", []) if isinstance(item, dict)]
        corrections.append(
            {
                "at": self._now(),
                "action": action,
                "template_name": template_name,
                "field": detection.field,
                "value": detection.value,
                "confidence": detection.confidence,
                "source": detection.source,
                "snippet": detection.snippet,
            }
        )
        profile["corrections"] = corrections
        learned_fields = set(profile.get("learned_fields", []))
        learned_fields.add(detection.field)
        profile["learned_fields"] = sorted(learned_fields)
        field_values = dict(profile.get("field_values", {}))
        if detection.value:
            field_values[detection.field] = detection.value
        profile["field_values"] = field_values
        profile["manual_values"] = {
            **{field: value for field, value in profile.get("manual_values", {}).items() if value},
            detection.field: detection.value,
        }
        profile["updated_at"] = self._now()
        profile["last_used_at"] = self._now()
        data[template_hash] = profile
        self.save(data)
        return profile

    def record_export(
        self,
        template_hash: str,
        template_name: str,
        output_path: str | Path,
    ) -> dict[str, Any]:
        data = self.load()
        profile = dict(data.get(template_hash, {}) if isinstance(data.get(template_hash, {}), dict) else {})
        history = [dict(item) for item in profile.get("history", []) if isinstance(item, dict)]
        history.append(
            {
                "at": self._now(),
                "event": "document_exported",
                "template_name": template_name,
                "output_path": str(Path(output_path)),
            }
        )
        profile["history"] = history
        profile["updated_at"] = self._now()
        profile["last_used_at"] = self._now()
        data[template_hash] = profile
        self.save(data)
        return profile

    def summarize(self, template_hash: str) -> dict[str, Any]:
        profile = self.load_profile(template_hash)
        return {
            "hash": profile.get("hash", template_hash),
            "template_name": profile.get("template_name", ""),
            "usage_count": profile.get("usage_count", 0),
            "learned_fields": profile.get("learned_fields", []),
            "required_fields": profile.get("required_fields", []),
            "corrections": profile.get("corrections", []),
            "history": profile.get("history", []),
        }

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")
