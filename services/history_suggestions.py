from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any
import re
import unicodedata

from services.history_manager import HistoryManager
from services.template_semantic_analyzer import SemanticDetection, TemplateSemanticAnalyzer
from services.user_session_store import UserSessionStore


SUGGESTABLE_FIELDS = (
    "{{CPF_CNPJ}}",
    "{{NACIONALIDADE}}",
    "{{PROFISSAO}}",
    "{{ESTADO_CIVIL}}",
    "{{CIDADE}}",
    "{{VENDEDOR}}",
    "{{EMPREENDIMENTO}}",
)

ANCHOR_FIELDS = ("{{COMPRADOR}}", "{{VENDEDOR}}")


@dataclass
class HistorySuggestion:
    field: str
    value: str
    source: str
    confidence: float
    reason: str
    current_value: str = ""
    status: str = "empty"
    anchor_field: str = ""
    anchor_value: str = ""
    template_hash: str = ""
    template_name: str = ""
    record_id: str = ""
    key: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "value": self.value,
            "source": self.source,
            "confidence": self.confidence,
            "reason": self.reason,
            "current_value": self.current_value,
            "status": self.status,
            "anchor_field": self.anchor_field,
            "anchor_value": self.anchor_value,
            "template_hash": self.template_hash,
            "template_name": self.template_name,
            "record_id": self.record_id,
            "key": self.key,
        }


class HistorySuggestions:
    def __init__(
        self,
        history_store: HistoryManager | None = None,
        session_store: UserSessionStore | None = None,
        semantic_analyzer: TemplateSemanticAnalyzer | None = None,
    ) -> None:
        self.history_store = history_store or HistoryManager()
        self.session_store = session_store or UserSessionStore()
        self.semantic_analyzer = semantic_analyzer or TemplateSemanticAnalyzer()

    def build_suggestions(
        self,
        current_values: dict[str, str],
        *,
        template_hash: str = "",
        ignored_keys: set[str] | None = None,
    ) -> dict[str, HistorySuggestion]:
        ignored_keys = ignored_keys or set()
        history_data = self.history_store.load()
        records = [record for record in history_data.get("records", []) if isinstance(record, dict)]
        if not records:
            return {}

        session = self.session_store.load()
        session_last_hash = str(session.get("last_template_hash", "") or "")
        template_profile = self.semantic_analyzer.load_template_mapping(template_hash) if template_hash else {}
        template_accepted = template_profile.get("accepted", {}) if isinstance(template_profile, dict) else {}

        anchors = self._anchors_from_values(current_values)

        if not anchors:
            return {}

        suggestions: dict[str, HistorySuggestion] = {}
        for anchor_field, anchor_value_raw in anchors:
            anchor_value = self._normalize(anchor_value_raw)
            if not anchor_value:
                continue
            anchor_records = self._collect_anchor_records(
                records,
                anchor_field=anchor_field,
                anchor_value=anchor_value,
                current_template_hash=template_hash,
                session_last_hash=session_last_hash,
            )
            for field in SUGGESTABLE_FIELDS:
                current_value = str(current_values.get(field, "")).strip()
                if field == anchor_field:
                    continue
                suggestion = self._suggest_for_field(
                    field=field,
                    anchor_field=anchor_field,
                    anchor_value_raw=anchor_value_raw,
                    current_value=current_value,
                    anchor_records=anchor_records,
                    ignored_keys=ignored_keys,
                    template_accepted=template_accepted if isinstance(template_accepted, dict) else {},
                    current_template_hash=template_hash,
                )
                if suggestion is None:
                    continue
                existing = suggestions.get(field)
                if existing is None or suggestion.confidence > existing.confidence:
                    suggestions[field] = suggestion

        return suggestions

    def _suggest_for_field(
        self,
        *,
        field: str,
        anchor_field: str,
        anchor_value_raw: str,
        current_value: str,
        anchor_records: list[dict[str, Any]],
        ignored_keys: set[str],
        template_accepted: dict[str, Any],
        current_template_hash: str,
    ) -> HistorySuggestion | None:
        candidate_scores: dict[str, float] = {}
        candidate_meta: dict[str, dict[str, Any]] = {}
        current_norm = self._normalize(current_value)

        for record, anchor_score in anchor_records:
            fields = record.get("fields", {})
            if not isinstance(fields, dict):
                continue
            value = str(fields.get(field, "")).strip()
            if not value:
                continue
            value_norm = self._normalize(value)
            if not value_norm or value_norm == current_norm:
                continue

            score = anchor_score
            if str(record.get("template_hash", "")) == current_template_hash and current_template_hash:
                score += 0.08
            if field in template_accepted:
                score += 0.03
            if self._same_value(value, current_value):
                continue

            candidate_scores[value] = candidate_scores.get(value, 0.0) + score
            meta = candidate_meta.setdefault(
                value,
                {
                    "record_id": str(record.get("id", "")),
                    "template_hash": str(record.get("template_hash", "")),
                    "template_name": str(record.get("template_name", "")),
                    "timestamp": str(record.get("timestamp", "")),
                },
            )
            if score > float(meta.get("score", 0.0)):
                meta["score"] = score

        if not candidate_scores:
            return None

        ranked = sorted(candidate_scores.items(), key=lambda item: item[1], reverse=True)
        top_value, top_score = ranked[0]
        second_score = ranked[1][1] if len(ranked) > 1 else 0.0
        top_score = min(0.98, top_score)

        if top_score < 0.72:
            return None
        if len(ranked) > 1 and second_score >= 0.66 and (top_score - second_score) < 0.10:
            return None

        suggestion_key = self._build_key(
            current_template_hash=current_template_hash,
            anchor_field=anchor_field,
            anchor_value=anchor_value_raw,
            field=field,
            value=top_value,
        )
        if suggestion_key in ignored_keys:
            return None

        status = "different" if current_value else "empty"
        reason = "Mesmo comprador encontrado em histórico anterior"
        if anchor_field == "{{VENDEDOR}}":
            reason = "Mesmo vendedor encontrado em histórico anterior"
        if current_template_hash and candidate_meta[top_value]["template_hash"] == current_template_hash:
            reason += " no mesmo template"

        return HistorySuggestion(
            field=field,
            value=top_value,
            source="history",
            confidence=round(top_score, 2),
            reason=reason,
            current_value=current_value,
            status=status,
            anchor_field=anchor_field,
            anchor_value=anchor_value_raw,
            template_hash=candidate_meta[top_value]["template_hash"],
            template_name=candidate_meta[top_value]["template_name"],
            record_id=candidate_meta[top_value]["record_id"],
            key=suggestion_key,
        )

    def _collect_anchor_records(
        self,
        records: list[dict[str, Any]],
        *,
        anchor_field: str,
        anchor_value: str,
        current_template_hash: str,
        session_last_hash: str,
    ) -> list[tuple[dict[str, Any], float]]:
        exact_matches: list[tuple[dict[str, Any], float]] = []
        fallback_matches: list[tuple[dict[str, Any], float]] = []
        for record in records:
            fields = record.get("fields", {})
            if not isinstance(fields, dict):
                continue
            record_anchor = str(fields.get(anchor_field, "")).strip()
            if not record_anchor:
                continue
            score = self._name_score(anchor_value, self._normalize(record_anchor))
            if score < 0.74:
                continue
            if current_template_hash and str(record.get("template_hash", "")) == current_template_hash:
                score += 0.08
            elif session_last_hash and str(record.get("template_hash", "")) == session_last_hash:
                score += 0.04
            if score >= 0.88:
                exact_matches.append((record, score))
            else:
                fallback_matches.append((record, score))
        return exact_matches or fallback_matches

    @staticmethod
    def _anchors_from_values(values: dict[str, str]) -> list[tuple[str, str]]:
        anchors: list[tuple[str, str]] = []
        for field in ANCHOR_FIELDS:
            value = str(values.get(field, "")).strip()
            if value:
                anchors.append((field, value))
        return anchors

    @staticmethod
    def _build_key(*, current_template_hash: str, anchor_field: str, anchor_value: str, field: str, value: str) -> str:
        return "|".join(
            [
                current_template_hash or "-",
                anchor_field,
                HistorySuggestions._normalize(anchor_value),
                field,
                HistorySuggestions._normalize(value),
            ]
        )

    @staticmethod
    def _same_value(left: str, right: str) -> bool:
        return HistorySuggestions._normalize(left) == HistorySuggestions._normalize(right)

    @staticmethod
    def _normalize(value: str) -> str:
        text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
        text = re.sub(r"[^0-9A-Za-z]+", " ", text.lower())
        text = " ".join(text.split())
        return text

    @classmethod
    def _name_score(cls, left: str, right: str) -> float:
        left_norm = cls._normalize(left)
        right_norm = cls._normalize(right)
        if not left_norm or not right_norm:
            return 0.0
        if left_norm == right_norm:
            return 1.0
        if cls._abbreviation_match(left_norm, right_norm):
            return 0.96
        if cls._abbreviation_match(right_norm, left_norm):
            return 0.96
        ratio = SequenceMatcher(None, left_norm, right_norm).ratio()
        if ratio >= 0.84:
            return ratio
        return 0.0

    @classmethod
    def _abbreviation_match(cls, short_text: str, long_text: str) -> bool:
        short_tokens = short_text.split()
        long_tokens = long_text.split()
        if len(short_tokens) > len(long_tokens):
            return False
        index = 0
        for short_token in short_tokens:
            matched = False
            while index < len(long_tokens):
                long_token = long_tokens[index]
                index += 1
                if long_token.startswith(short_token):
                    matched = True
                    break
                if len(short_token) == 1 and long_token.startswith(short_token[0]):
                    matched = True
                    break
            if not matched:
                return False
        return True
