from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from docx import Document


FIELD_LABELS = {
    "{{COMPRADOR}}": "Nome Completo",
    "{{NACIONALIDADE}}": "Nacionalidade",
    "{{PROFISSAO}}": "Profiss\u00e3o",
    "{{ESTADO_CIVIL}}": "Estado Civil",
    "{{CPF_CNPJ}}": "CPF/CNPJ",
    "{{LOTE}}": "Lote/Unidade",
    "{{QUADRA}}": "Quadra",
    "{{EMPREENDIMENTO}}": "Empreendimento",
    "{{VENDEDOR}}": "Nome do Vendedor",
    "{{CIDADE}}": "Cidade",
    "{{DATA}}": "Data",
}

SUPPORTED_FIELDS = tuple(FIELD_LABELS)
LETTER_RANGE = r"A-Za-z\u00C0-\u017F"
UPPER_RANGE = r"A-Z\u00C0-\u00DE"
CPF_CNPJ_PATTERN = r"(?:\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{3}\.\d{3}\.\d{3}-\d{2}|[\d./-]{11,20})"
DATE_PATTERN = rf"\d{{1,2}}\s+de\s+[{LETTER_RANGE}]+\s+de\s+\d{{4}}"
NAME_PATTERN = rf"[{UPPER_RANGE}][{UPPER_RANGE}0-9&.'\- ]{{3,120}}"


@dataclass
class SemanticDetection:
    field: str
    value: str
    confidence: float
    source: str
    snippet: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SemanticDetection":
        return cls(
            field=str(data.get("field", "")),
            value=str(data.get("value", "")),
            confidence=float(data.get("confidence", 0.0)),
            source=str(data.get("source", "")),
            snippet=str(data.get("snippet", "")),
        )


def _default_mapping_file() -> Path:
    if getattr(sys, "frozen", False):
        local_app_data = os.getenv("LOCALAPPDATA")
        base_dir = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
        return base_dir / "DocFillPro" / "data" / "template_semantic_mappings.json"
    return Path(__file__).resolve().parent.parent / "data" / "template_semantic_mappings.json"


def _resource_root() -> Path:
    if getattr(sys, "frozen", False):
        frozen_root = getattr(sys, "_MEIPASS", None)
        if frozen_root:
            return Path(frozen_root)
    return Path(__file__).resolve().parent.parent


class TemplateSemanticAnalyzer:
    """Infers values for the fixed DocFill Pro UI fields from a DOCX template."""

    DEFAULT_FILE = _default_mapping_file()

    def __init__(self, file_path: str | Path | None = None) -> None:
        self.file_path = Path(file_path) if file_path else self.DEFAULT_FILE
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.seed_file = _resource_root() / "data" / "template_semantic_mappings.json"
        if not self.file_path.exists():
            self._initialize_storage()

    def analyze(self, template_path: str | Path) -> dict[str, SemanticDetection]:
        path = Path(template_path)
        template_hash = self.template_hash(path)
        blocks = self._collect_blocks(path)
        full_text = "\n".join(blocks)

        auto_detections: dict[str, SemanticDetection] = {}
        self._detect_placeholders(full_text, auto_detections)
        self._detect_structured_declaration(full_text, auto_detections)
        self._detect_contextual_fields(full_text, auto_detections)

        saved = self.load_template_mapping(template_hash)
        accepted = saved.get("accepted", {}) if isinstance(saved, dict) else {}
        detections = dict(auto_detections)
        for field, data in accepted.items():
            if field in SUPPORTED_FIELDS and isinstance(data, dict):
                detection = SemanticDetection.from_dict(data)
                if detection.value:
                    detections[field] = detection

        self.save_detections(template_hash, path.name, auto_detections, detections)
        return detections

    def save_detections(
        self,
        template_hash: str,
        template_name: str,
        auto_detections: dict[str, SemanticDetection],
        detections: dict[str, SemanticDetection],
    ) -> None:
        data = self._load_all()
        current = data.get(template_hash, {})
        data[template_hash] = {
            **current,
            "template_name": template_name,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "usage_count": int(current.get("usage_count", 0)) + 1,
            "last_used_at": datetime.now().isoformat(timespec="seconds"),
            "auto_detections": {field: detection.to_dict() for field, detection in auto_detections.items()},
            "detections": {field: detection.to_dict() for field, detection in detections.items()},
            "accepted": current.get("accepted", {}),
            "history": current.get("history", []),
        }
        self._atomic_write(data)

    def accept_detection(self, template_hash: str, detection: SemanticDetection) -> None:
        data = self._load_all()
        item = data.setdefault(template_hash, {})
        accepted = item.setdefault("accepted", {})
        accepted[detection.field] = detection.to_dict()
        history = item.setdefault("history", [])
        history.append(
            {
                "at": datetime.now().isoformat(timespec="seconds"),
                "action": "accept",
                "field": detection.field,
                "value": detection.value,
                "confidence": detection.confidence,
                "source": detection.source,
            }
        )
        item["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self._atomic_write(data)

    def save_manual_value(self, template_hash: str, field: str, value: str) -> SemanticDetection:
        detection = SemanticDetection(
            field=field,
            value=value.strip(),
            confidence=1.0,
            source="manual: correcao do usuario",
            snippet=value.strip(),
        )
        self.accept_detection(template_hash, detection)
        return detection

    def load_template_mapping(self, template_hash: str) -> dict[str, Any]:
        return dict(self._load_all().get(template_hash, {}))

    @staticmethod
    def template_hash(template_path: str | Path) -> str:
        handle = hashlib.sha256()
        with Path(template_path).open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                handle.update(chunk)
        return handle.hexdigest()

    @staticmethod
    def suggestion_values(detections: dict[str, SemanticDetection]) -> dict[str, str]:
        return {
            field: detection.value
            for field, detection in detections.items()
            if detection.value and field in SUPPORTED_FIELDS
        }

    def _detect_placeholders(self, text: str, detections: dict[str, SemanticDetection]) -> None:
        for match in re.finditer(r"\{\{[^{}]+\}\}", text):
            marker = self._normalize_marker(match.group(0))
            if marker not in SUPPORTED_FIELDS or marker in detections:
                continue
            detections[marker] = SemanticDetection(
                field=marker,
                value="",
                confidence=0.99,
                source="placeholder",
                snippet=self._snippet(text, match.start(), match.end()),
            )

    def _detect_structured_declaration(self, text: str, detections: dict[str, SemanticDetection]) -> None:
        pattern = re.compile(
            rf"(?P<comprador>{NAME_PATTERN}),\s*"
            rf"(?P<nacionalidade>[{LETTER_RANGE} ]{{4,40}}),\s*"
            rf"(?P<profissao>[{LETTER_RANGE}0-9 .'\-/]{{3,70}}),\s*"
            rf"(?P<estado_civil>[{LETTER_RANGE} ]{{4,45}}),\s*"
            rf"portador(?:a)?\s+do\s+(?:CPF|CNPJ)\s+n?[\u00ba\u00b0o.]?\s*(?P<cpf>{CPF_CNPJ_PATTERN})"
            rf".{{0,180}}?\bLote\s+(?P<lote>[A-Z0-9][A-Z0-9./\-]*)"
            rf"\s+Quadra\s+(?P<quadra>[A-Z0-9][A-Z0-9./\-]*)"
            rf"\s+do\s+(?P<empreendimento>{NAME_PATTERN})(?=,|\s+adquirido|\.)"
            rf".{{0,180}}?do\(a\)\s+(?P<vendedor>{NAME_PATTERN})(?=,|\s+para|\.)",
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(text)
        if not match:
            return

        fields = {
            "comprador": "{{COMPRADOR}}",
            "nacionalidade": "{{NACIONALIDADE}}",
            "profissao": "{{PROFISSAO}}",
            "estado_civil": "{{ESTADO_CIVIL}}",
            "cpf": "{{CPF_CNPJ}}",
            "lote": "{{LOTE}}",
            "quadra": "{{QUADRA}}",
            "empreendimento": "{{EMPREENDIMENTO}}",
            "vendedor": "{{VENDEDOR}}",
        }
        for group, field in fields.items():
            confidence = 0.94 if group in {"cpf", "lote", "quadra"} else 0.9
            self._add_detection(
                detections,
                field,
                match.group(group),
                confidence,
                "context: qualificacao estruturada",
                self._snippet(text, match.start(group), match.end(group)),
            )

    def _detect_contextual_fields(self, text: str, detections: dict[str, SemanticDetection]) -> None:
        context_patterns = [
            (
                "{{COMPRADOR}}",
                rf"(?:permituta|permuta|permutante|comprador(?:a)?|adquirente)\s+(?:do\(a\)\s+|da\s+|do\s+)?(?P<value>{NAME_PATTERN})(?=,|\s+portador|\s+na\s+qualidade|\.|\n|$)",
                0.88,
                "context: permituta do(a)",
            ),
            (
                "{{CPF_CNPJ}}",
                rf"(?:CPF|CNPJ)\s+n?[\u00ba\u00b0o.]?\s*(?P<value>{CPF_CNPJ_PATTERN})",
                0.86,
                "context: CPF/CNPJ",
            ),
            ("{{LOTE}}", r"\bLote\s+(?P<value>[A-Z0-9][A-Z0-9./\-]*)", 0.92, "context: Lote"),
            ("{{QUADRA}}", r"\bQuadra\s+(?P<value>[A-Z0-9][A-Z0-9./\-]*)", 0.92, "context: Quadra"),
            (
                "{{EMPREENDIMENTO}}",
                rf"(?P<value>(?:LOTEAMENTO|CONDOM[\u00cdI]NIO|RESIDENCIAL|EDIF[\u00cdI]CIO|ALPHAVILLE)[{UPPER_RANGE}0-9 .'/-]{{6,120}})(?=,|\.|\s+adquirido|\s+localizado|\n|$)",
                0.86,
                "context: empreendimento",
            ),
            (
                "{{VENDEDOR}}",
                rf"(?:adquirido|alienado|cedido|vendido).{{0,80}}?do\(a\)\s+(?P<value>{NAME_PATTERN})(?=,|\s+para|\.)",
                0.86,
                "context: adquirido do(a)",
            ),
            ("{{DATA}}", rf"(?P<value>{DATE_PATTERN})", 0.82, "context: data por extenso"),
        ]

        for field, pattern, confidence, source in context_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if not match:
                continue
            self._add_detection(
                detections,
                field,
                match.group("value"),
                confidence,
                source,
                self._snippet(text, match.start("value"), match.end("value")),
            )

        city_date = re.search(
            rf"(?P<cidade>[{UPPER_RANGE}][{UPPER_RANGE} .'/-]{{2,80}}),\s*(?P<data>{DATE_PATTERN})",
            text,
            re.IGNORECASE,
        )
        if city_date:
            self._add_detection(
                detections,
                "{{CIDADE}}",
                city_date.group("cidade"),
                0.9,
                "context: cidade antes da data",
                self._snippet(text, city_date.start("cidade"), city_date.end("cidade")),
            )
            self._add_detection(
                detections,
                "{{DATA}}",
                city_date.group("data"),
                0.92,
                "context: data apos cidade",
                self._snippet(text, city_date.start("data"), city_date.end("data")),
            )
        else:
            city_match = re.search(r"\bRIBEIR[\u00c3A]O\s+PRETO\b", text, re.IGNORECASE)
            if city_match:
                self._add_detection(
                    detections,
                    "{{CIDADE}}",
                    city_match.group(0),
                    0.68,
                    "context: cidade conhecida",
                    self._snippet(text, city_match.start(), city_match.end()),
                )

    def _add_detection(
        self,
        detections: dict[str, SemanticDetection],
        field: str,
        value: str,
        confidence: float,
        source: str,
        snippet: str,
    ) -> None:
        if field not in SUPPORTED_FIELDS:
            return
        clean_value = self._clean_value(value)
        if not clean_value:
            return
        current = detections.get(field)
        if current and current.value and current.confidence >= confidence:
            return
        detections[field] = SemanticDetection(
            field=field,
            value=clean_value,
            confidence=round(min(1.0, max(0.0, confidence)), 2),
            source=source,
            snippet=snippet,
        )

    def _collect_blocks(self, template_path: Path) -> list[str]:
        document = Document(template_path)
        blocks: list[str] = []
        for paragraph in document.paragraphs:
            self._append_block(blocks, paragraph.text)
        for table in document.tables:
            self._append_table(blocks, table)
        for part in self._iter_section_parts(document):
            for paragraph in part.paragraphs:
                self._append_block(blocks, paragraph.text)
            for table in part.tables:
                self._append_table(blocks, table)
        return blocks

    @classmethod
    def _append_table(cls, blocks: list[str], table: Any) -> None:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    cls._append_block(blocks, paragraph.text)
                for nested_table in cell.tables:
                    cls._append_table(blocks, nested_table)

    @staticmethod
    def _append_block(blocks: list[str], text: str) -> None:
        clean = " ".join((text or "").split())
        if clean:
            blocks.append(clean)

    @staticmethod
    def _iter_section_parts(document: Any) -> Any:
        seen: set[int] = set()
        attrs = (
            "header",
            "first_page_header",
            "even_page_header",
            "footer",
            "first_page_footer",
            "even_page_footer",
        )
        for section in document.sections:
            for attr_name in attrs:
                part = getattr(section, attr_name, None)
                if part is None:
                    continue
                element_id = id(part._element)
                if element_id in seen:
                    continue
                seen.add(element_id)
                yield part

    @staticmethod
    def _snippet(text: str, start: int, end: int, radius: int = 70) -> str:
        left = max(0, start - radius)
        right = min(len(text), end + radius)
        snippet = " ".join(text[left:right].split())
        if left > 0:
            snippet = "..." + snippet
        if right < len(text):
            snippet += "..."
        return snippet

    @staticmethod
    def _clean_value(value: str) -> str:
        clean = " ".join((value or "").split())
        clean = clean.strip(" ,.;:-")
        return clean

    @staticmethod
    def _normalize_marker(marker: str) -> str:
        marker_text = marker.strip().upper()
        marker_text = marker_text.removeprefix("{{").removesuffix("}}").strip()
        marker_text = marker_text.strip("{}").strip()
        return f"{{{{{marker_text}}}}}" if marker_text else ""

    def _load_all(self) -> dict[str, Any]:
        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return {}

    def _atomic_write(self, data: dict[str, Any]) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.file_path.parent, delete=False) as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            temp_path = Path(handle.name)
        os.replace(temp_path, self.file_path)

    def _initialize_storage(self) -> None:
        try:
            if self.seed_file.exists():
                self._copy_seed_file(self.seed_file)
                return
        except OSError:
            pass
        self._atomic_write({})

    def _copy_seed_file(self, source: Path) -> None:
        try:
            content = source.read_text(encoding="utf-8")
        except OSError:
            self._atomic_write({})
            return
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.file_path.parent, delete=False) as handle:
            handle.write(content)
            temp_path = Path(handle.name)
        os.replace(temp_path, self.file_path)
