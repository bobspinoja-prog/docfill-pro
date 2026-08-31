from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from PIL import Image

from services.field_extractor import MARKER_BY_FIELD, extract_fields
from services.template_semantic_analyzer import SUPPORTED_FIELDS, SemanticDetection

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover - exercised only when dependency is missing.
    fitz = None


RectTuple = tuple[float, float, float, float]


@dataclass(frozen=True)
class PDFTextBlock:
    page_index: int
    rect: RectTuple
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PDFRenderPage:
    page_index: int
    width: float
    height: float
    image: Image.Image
    blocks: list[PDFTextBlock] = field(default_factory=list)


@dataclass(frozen=True)
class PDFManualArea:
    marker: str
    page_index: int
    rect: RectTuple
    selected_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "marker": self.marker,
            "page_index": self.page_index,
            "rect": list(self.rect),
            "selected_text": self.selected_text,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PDFManualArea":
        rect = data.get("rect", (0, 0, 0, 0))
        values = list(rect)[:4] if isinstance(rect, (list, tuple)) else [0, 0, 0, 0]
        while len(values) < 4:
            values.append(0)
        return cls(
            marker=str(data.get("marker", "")),
            page_index=int(data.get("page_index", 0) or 0),
            rect=_normalize_rect_tuple(tuple(float(value) for value in values[:4])),
            selected_text=str(data.get("selected_text", "")),
        )


@dataclass
class PDFGenerationReport:
    output_path: Path
    manual_fields: list[str] = field(default_factory=list)
    auto_fields: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_path": str(self.output_path),
            "manual_fields": list(dict.fromkeys(self.manual_fields)),
            "auto_fields": list(dict.fromkeys(self.auto_fields)),
            "skipped": list(dict.fromkeys(self.skipped)),
            "warnings": list(dict.fromkeys(self.warnings)),
        }


@dataclass(frozen=True)
class _PDFEdit:
    page_index: int
    rect: RectTuple
    text: str
    marker: str
    source: str


def pdf_support_available() -> bool:
    return fitz is not None


def ensure_pdf_support() -> None:
    if fitz is None:
        raise RuntimeError(
            "Suporte a PDF indisponivel. Instale a dependencia PyMuPDF com: pip install PyMuPDF"
        )


class PDFHandler:
    """Reads, renders, annotates, and fills PDF templates."""

    def __init__(self, template_path: str | Path) -> None:
        ensure_pdf_support()
        self.template_path = Path(template_path)
        self._document: Any | None = None
        self._blocks: list[PDFTextBlock] | None = None
        self._page_texts: list[str] | None = None
        self._analysis: dict[str, Any] | None = None
        self._rendered_pages_cache: dict[tuple[int, int | None], list[PDFRenderPage]] = {}

    def extract_text(self, replacements: dict[str, str] | None = None) -> str:
        replacements = replacements or {}
        text = "\n\n".join(text for text in self._get_page_texts() if text.strip())
        for source, target in replacements.items():
            if source:
                text = text.replace(str(source), "" if target is None else str(target))
        return text

    def field_text(self) -> str:
        text = self.extract_text({})
        return re.sub(
            r"^\s*DECLARA(?:C|\u00c7)(?:AO|\u00c3O|\u00c7\u00c3O)?\s+",
            "",
            text,
            count=1,
            flags=re.IGNORECASE,
        )

    def analyze_template(self) -> dict[str, Any]:
        if self._analysis is None:
            self._analysis = self._build_analysis()
        return {
            **self._analysis,
            "placeholders": list(self._analysis["placeholders"]),
            "areas": list(self._analysis["areas"]),
            "summary": list(self._analysis["summary"]),
        }

    def suggest_values(self) -> dict[str, str]:
        return extract_fields(self.field_text()).as_marker_values(min_confidence=0.60)

    def detect_fields(self) -> dict[str, SemanticDetection]:
        detections: dict[str, SemanticDetection] = {}
        extraction = extract_fields(self.field_text())
        for field_name, item in extraction.fields.items():
            marker = MARKER_BY_FIELD.get(field_name)
            if marker not in SUPPORTED_FIELDS or not item.value:
                continue
            detections[marker] = SemanticDetection(
                field=marker,
                value=item.value,
                confidence=item.confidence,
                source=f"pdf:{item.source}",
                snippet=item.evidence,
            )
        return detections

    def render_pages(self, zoom_percent: int = 100, max_pages: int | None = None) -> list[PDFRenderPage]:
        cache_key = (zoom_percent, max_pages)
        cached = self._rendered_pages_cache.get(cache_key)
        if cached is not None:
            return cached

        document = self._get_document()
        scale = max(0.5, min(3.0, zoom_percent / 100))
        matrix = fitz.Matrix(scale, scale)
        limit = document.page_count if max_pages is None else min(max_pages, document.page_count)
        blocks_by_page = self._blocks_by_page()
        pages: list[PDFRenderPage] = []
        for page_index in range(limit):
            page = document[page_index]
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            rect = page.rect
            pages.append(
                PDFRenderPage(
                    page_index=page_index,
                    width=float(rect.width),
                    height=float(rect.height),
                    image=image,
                    blocks=blocks_by_page.get(page_index, []),
                )
            )
        self._rendered_pages_cache[cache_key] = pages
        return pages

    def generate_filled_pdf(
        self,
        output_path: str | Path,
        values: dict[str, str],
        manual_areas: dict[str, list[PDFManualArea | dict[str, Any]]] | None = None,
        detections: dict[str, SemanticDetection] | None = None,
        replace_detected: bool = True,
    ) -> PDFGenerationReport:
        output = Path(output_path)
        report = PDFGenerationReport(output_path=output)
        edits = self._build_manual_edits(values, manual_areas or {}, report)
        if replace_detected:
            edits.extend(self._build_detection_edits(values, detections or {}, report, manual_areas or {}))
        self._write_pdf_with_edits(output, edits, report)
        return report

    def generate_marked_pdf(
        self,
        output_path: str | Path,
        manual_areas: dict[str, list[PDFManualArea | dict[str, Any]]] | None = None,
        detections: dict[str, SemanticDetection] | None = None,
    ) -> PDFGenerationReport:
        marker_values = {marker: marker for marker in SUPPORTED_FIELDS}
        return self.generate_filled_pdf(
            output_path,
            marker_values,
            manual_areas=manual_areas,
            detections=detections,
            replace_detected=True,
        )

    def text_for_rect(self, page_index: int, rect: RectTuple) -> str:
        target = _normalize_rect_tuple(rect)
        values = [
            block.text
            for block in self._blocks_by_page().get(page_index, [])
            if _rects_intersect(block.rect, target)
        ]
        return " ".join(" ".join(value.split()) for value in values if value.strip()).strip()

    @staticmethod
    def template_hash(template_path: str | Path) -> str:
        handle = hashlib.sha256()
        with Path(template_path).open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                handle.update(chunk)
        return handle.hexdigest()

    def _get_document(self) -> Any:
        if not self.template_path.exists():
            raise FileNotFoundError("Arquivo PDF nao encontrado.")
        if self._document is None:
            self._document = fitz.open(self.template_path)
        return self._document

    def _get_page_texts(self) -> list[str]:
        if self._page_texts is None:
            document = self._get_document()
            self._page_texts = [document[index].get_text("text").strip() for index in range(document.page_count)]
        return self._page_texts

    def _get_blocks(self) -> list[PDFTextBlock]:
        if self._blocks is not None:
            return self._blocks
        document = self._get_document()
        blocks: list[PDFTextBlock] = []
        for page_index in range(document.page_count):
            page = document[page_index]
            for raw_block in page.get_text("blocks"):
                if len(raw_block) >= 7 and int(raw_block[6]) != 0:
                    continue
                text = _clean_block_text(str(raw_block[4] if len(raw_block) > 4 else ""))
                if not text:
                    continue
                blocks.append(
                    PDFTextBlock(
                        page_index=page_index,
                        rect=_normalize_rect_tuple(tuple(float(value) for value in raw_block[:4])),
                        text=text,
                    )
                )
        self._blocks = blocks
        return blocks

    def _blocks_by_page(self) -> dict[int, list[PDFTextBlock]]:
        pages: dict[int, list[PDFTextBlock]] = {}
        for block in self._get_blocks():
            pages.setdefault(block.page_index, []).append(block)
        return pages

    def _build_analysis(self) -> dict[str, Any]:
        document = self._get_document()
        text = self.extract_text({})
        placeholders = list(dict.fromkeys(re.findall(r"\{\{[^{}]+\}\}", text)))
        blocks_by_page = self._blocks_by_page()
        areas = [
            f"Pagina {page_index + 1}: {len(blocks)} blocos de texto"
            for page_index, blocks in sorted(blocks_by_page.items())
        ]
        return {
            "template": self.template_path.name,
            "pages": document.page_count,
            "text_blocks": len(self._get_blocks()),
            "placeholders": placeholders,
            "areas": areas,
            "summary": [
                f"Paginas: {document.page_count}",
                f"Blocos de texto: {len(self._get_blocks())}",
                f"Marcadores unicos: {len(placeholders)}",
            ],
        }

    def _build_manual_edits(
        self,
        values: dict[str, str],
        manual_areas: dict[str, list[PDFManualArea | dict[str, Any]]],
        report: PDFGenerationReport,
    ) -> list[_PDFEdit]:
        edits: list[_PDFEdit] = []
        for marker, area_items in manual_areas.items():
            target = str(values.get(marker, "")).strip()
            if not target:
                report.skipped.append(f"{marker}: sem valor para area manual")
                continue
            for area in _coerce_areas(marker, area_items):
                edits.append(_PDFEdit(area.page_index, area.rect, target, marker, "manual"))
                report.manual_fields.append(marker)
        return edits

    def _build_detection_edits(
        self,
        values: dict[str, str],
        detections: dict[str, SemanticDetection],
        report: PDFGenerationReport,
        manual_areas: dict[str, list[PDFManualArea | dict[str, Any]]],
    ) -> list[_PDFEdit]:
        edits: list[_PDFEdit] = []
        manual_markers = {marker for marker, areas in manual_areas.items() if areas}
        document = self._get_document()
        for marker, detection in detections.items():
            if marker in manual_markers:
                continue
            source = str(getattr(detection, "value", "") or "").strip()
            target = str(values.get(marker, "")).strip()
            if not source or not target or source == target:
                continue
            if float(getattr(detection, "confidence", 0.0) or 0.0) < 0.60:
                report.skipped.append(f"{marker}: confianca baixa para substituicao PDF")
                continue

            matches: list[tuple[int, RectTuple]] = []
            for page_index in range(document.page_count):
                page = document[page_index]
                for match_rect in page.search_for(source):
                    matches.append((page_index, _fitz_rect_to_tuple(match_rect)))
            if not matches:
                report.skipped.append(f"{marker}: texto original nao encontrado no PDF")
                continue
            if len(matches) > 4 and marker not in {"{{COMPRADOR}}", "{{VENDEDOR}}"}:
                report.skipped.append(f"{marker}: texto aparece {len(matches)} vezes no PDF")
                continue
            for page_index, rect in matches:
                edits.append(_PDFEdit(page_index, _expand_rect(rect, 1.2), target, marker, "detected"))
                report.auto_fields.append(marker)
        return edits

    def _write_pdf_with_edits(
        self,
        output_path: Path,
        edits: list[_PDFEdit],
        report: PDFGenerationReport,
    ) -> None:
        if self.template_path.resolve() == output_path.resolve():
            raise ValueError("O arquivo gerado nao pode sobrescrever o PDF original.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        document = fitz.open(self.template_path)
        edits_by_page: dict[int, list[_PDFEdit]] = {}
        for edit in edits:
            if 0 <= edit.page_index < document.page_count:
                edits_by_page.setdefault(edit.page_index, []).append(edit)
            else:
                report.skipped.append(f"{edit.marker}: pagina invalida {edit.page_index + 1}")

        for page_index, page_edits in edits_by_page.items():
            page = document[page_index]
            for edit in page_edits:
                rect = _clamp_rect(edit.rect, page.rect)
                if rect.is_empty or rect.width < 2 or rect.height < 2:
                    report.skipped.append(f"{edit.marker}: area PDF invalida")
                    continue
                page.add_redact_annot(rect, fill=(1, 1, 1))
            page.apply_redactions()
            for edit in page_edits:
                rect = _clamp_rect(edit.rect, page.rect)
                if rect.is_empty or rect.width < 2 or rect.height < 2:
                    continue
                self._insert_text(page, rect, edit.text, report, edit.marker)

        document.save(output_path, garbage=4, deflate=True)
        document.close()

    @staticmethod
    def _insert_text(page: Any, rect: Any, text: str, report: PDFGenerationReport, marker: str) -> None:
        font_size = min(11.0, max(6.0, rect.height * 0.55))
        for attempt in range(8):
            size = max(5.0, font_size - (attempt * 0.75))
            result = page.insert_textbox(
                rect,
                text,
                fontsize=size,
                fontname="helv",
                color=(0, 0, 0),
                align=0,
            )
            if result >= 0:
                return
        report.warnings.append(f"{marker}: texto pode nao caber na area selecionada")


def _coerce_areas(marker: str, areas: Iterable[PDFManualArea | dict[str, Any]]) -> list[PDFManualArea]:
    result: list[PDFManualArea] = []
    for item in areas:
        if isinstance(item, PDFManualArea):
            result.append(item)
            continue
        if isinstance(item, dict):
            payload = {"marker": marker, **item}
            result.append(PDFManualArea.from_dict(payload))
    return result


def _clean_block_text(text: str) -> str:
    return " ".join((text or "").split())


def _normalize_rect_tuple(rect: tuple[float, float, float, float]) -> RectTuple:
    x0, y0, x1, y1 = rect
    return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)


def _fitz_rect_to_tuple(rect: Any) -> RectTuple:
    return float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)


def _expand_rect(rect: RectTuple, amount: float) -> RectTuple:
    x0, y0, x1, y1 = rect
    return x0 - amount, y0 - amount, x1 + amount, y1 + amount


def _rects_intersect(left: RectTuple, right: RectTuple) -> bool:
    left = _normalize_rect_tuple(left)
    right = _normalize_rect_tuple(right)
    return not (left[2] < right[0] or right[2] < left[0] or left[3] < right[1] or right[3] < left[1])


def _clamp_rect(rect: RectTuple, bounds: Any) -> Any:
    x0, y0, x1, y1 = _normalize_rect_tuple(rect)
    return fitz.Rect(
        max(float(bounds.x0), x0),
        max(float(bounds.y0), y0),
        min(float(bounds.x1), x1),
        min(float(bounds.y1), y1),
    )
