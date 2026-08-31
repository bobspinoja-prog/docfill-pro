from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from services.template_semantic_analyzer import SemanticDetection, SUPPORTED_FIELDS


FIELD_CONFIDENCE_THRESHOLDS = {
    "{{COMPRADOR}}": 0.86,
    "{{NACIONALIDADE}}": 0.80,
    "{{PROFISSAO}}": 0.80,
    "{{ESTADO_CIVIL}}": 0.80,
    "{{CPF_CNPJ}}": 0.90,
    "{{LOTE}}": 0.88,
    "{{QUADRA}}": 0.88,
    "{{EMPREENDIMENTO}}": 0.84,
    "{{VENDEDOR}}": 0.86,
    "{{CIDADE}}": 0.82,
    "{{DATA}}": 0.88,
}

FIELD_KIND = {
    "{{COMPRADOR}}": "name",
    "{{NACIONALIDADE}}": "word",
    "{{PROFISSAO}}": "word",
    "{{ESTADO_CIVIL}}": "word",
    "{{CPF_CNPJ}}": "id",
    "{{LOTE}}": "lot",
    "{{QUADRA}}": "lot",
    "{{EMPREENDIMENTO}}": "name",
    "{{VENDEDOR}}": "name",
    "{{CIDADE}}": "city",
    "{{DATA}}": "date",
}


@dataclass
class BlockedSemanticReplacement:
    field: str
    source: str
    target: str
    reason: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "source": self.source,
            "target": self.target,
            "reason": self.reason,
            "confidence": self.confidence,
        }


@dataclass
class SafeSemanticReplacementResult:
    safe_replacements: dict[str, str] = field(default_factory=dict)
    blocked_replacements: list[BlockedSemanticReplacement] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def build_safe_semantic_replacements(
    detected_fields: dict[str, SemanticDetection | dict[str, Any]],
    manual_values: dict[str, str],
    placeholder_replacements: dict[str, str],
    document_text: str,
) -> SafeSemanticReplacementResult:
    result = SafeSemanticReplacementResult()
    placeholder_fields = _normalize_placeholder_fields(placeholder_replacements)
    normalized_text = _normalize_text(document_text)

    for field, detection in detected_fields.items():
        if field not in SUPPORTED_FIELDS or field in placeholder_fields:
            continue

        detection = _coerce_detection(field, detection)
        if detection is None:
            continue

        source = _normalize_text(detection.value)
        target = _normalize_text(manual_values.get(field, ""))
        if not source or not target or source == target:
            continue

        if detection.source.startswith("manual:"):
            _block(result, field, source, target, detection.confidence, "correção manual não gera substituição literal")
            continue

        if detection.confidence < FIELD_CONFIDENCE_THRESHOLDS.get(field, 0.85):
            _block(result, field, source, target, detection.confidence, "confiança abaixo do limite")
            continue

        if not detection.source and not detection.snippet:
            _block(result, field, source, target, detection.confidence, "sem trecho de origem conhecido")
            continue

        matches = list(_safe_matches(field, source, normalized_text))
        if not matches:
            _block(result, field, source, target, detection.confidence, "valor antigo não encontrado no documento")
            continue
        if len(matches) > 1:
            warning = (
                f"{_field_label(field)} não foi substituído automaticamente porque o valor aparece em múltiplos contextos. "
                "Revise o mapeamento."
            )
            result.warnings.append(warning)
            _block(result, field, source, target, detection.confidence, "substituição ambígua")
            continue

        if field in {"{{COMPRADOR}}", "{{VENDEDOR}}", "{{EMPREENDIMENTO}}"} and not _looks_like_stable_name(source):
            _block(result, field, source, target, detection.confidence, "nome curto ou instável para replace literal")
            continue

        result.safe_replacements[source] = target

    return result


def _coerce_detection(field: str, value: SemanticDetection | dict[str, Any]) -> SemanticDetection | None:
    if isinstance(value, SemanticDetection):
        return value
    if isinstance(value, dict):
        return SemanticDetection.from_dict({"field": field, **value})
    return None


def _block(
    result: SafeSemanticReplacementResult,
    field: str,
    source: str,
    target: str,
    confidence: float,
    reason: str,
) -> None:
    result.blocked_replacements.append(
        BlockedSemanticReplacement(
            field=field,
            source=source,
            target=target,
            reason=reason,
            confidence=round(confidence, 2),
        )
    )


def _field_label(field: str) -> str:
    return field.removeprefix("{{").removesuffix("}}").replace("_", " ")


def _normalize_placeholder_fields(replacements: dict[str, str]) -> set[str]:
    fields: set[str] = set()
    for key in replacements:
        normalized = key.strip().upper()
        if not normalized.startswith("{{"):
            continue
        if not normalized.endswith("}}"):
            continue
        fields.add(normalized)
    return fields


def _normalize_text(value: str) -> str:
    return " ".join((value or "").split())


def _safe_matches(field: str, source: str, document_text: str) -> list[re.Match[str]]:
    if not source or not document_text:
        return []

    escaped = re.escape(source)
    pattern = r"(?<![0-9A-Za-zÀ-ÿ])" + escaped + r"(?![0-9A-Za-zÀ-ÿ])"

    matches = list(re.finditer(pattern, document_text, flags=re.IGNORECASE))
    if FIELD_KIND.get(field) == "name":
        matches = [match for match in matches if _name_match_is_clean(document_text, match)]
    return matches


def _name_match_is_clean(document_text: str, match: re.Match[str]) -> bool:
    before = document_text[match.start() - 1] if match.start() > 0 else ""
    after = document_text[match.end()] if match.end() < len(document_text) else ""
    if before in "-/" or after in "-/":
        return False
    return True


def _looks_like_stable_name(source: str) -> bool:
    tokens = [part for part in source.split() if part]
    return len(tokens) >= 2 and len(source) >= 8
