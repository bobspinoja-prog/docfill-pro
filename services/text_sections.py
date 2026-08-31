from __future__ import annotations

import re
from dataclasses import dataclass


SECTION_NAMES = ("preambulo", "corpo", "paragrafo_final", "data", "assinaturas")
LETTER_RANGE = r"A-Za-z\u00C0-\u017F\?"
DATE_PATTERN = rf"\d{{1,2}}\s+de\s+[{LETTER_RANGE}]+\s+de\s+\d{{4}}"
CITY_DATE_PATTERN = re.compile(
    rf"(?:^|[.;]\s+)(?P<cidade>[{LETTER_RANGE}][{LETTER_RANGE} .'\-]{{2,80}})\s*,\s*(?P<data>{DATE_PATTERN})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TextSection:
    name: str
    text: str
    start_index: int
    end_index: int

    @property
    def is_empty(self) -> bool:
        return self.start_index >= self.end_index or not self.text.strip()


@dataclass(frozen=True)
class DocumentSections:
    text: str
    sections: dict[str, TextSection]

    def get(self, name: str) -> TextSection:
        return self.sections.get(name, TextSection(name, "", 0, 0))

    def to_dict(self) -> dict[str, dict[str, int | str]]:
        return {
            name: {
                "text": section.text,
                "start_index": section.start_index,
                "end_index": section.end_index,
            }
            for name, section in self.sections.items()
        }


def split_text_sections(text: str) -> DocumentSections:
    value = text or ""
    date_match = _last_match(CITY_DATE_PATTERN, value)
    data_start = date_match.start("cidade") if date_match else len(value)
    data_end = date_match.end("data") if date_match else data_start

    recebi_match = re.search(r"\bA\)\s*RECEBI\b", value, flags=re.IGNORECASE)
    final_match = re.search(r"\bAssim,\s+por\s+todo\s+o\s+exposto\b", value, flags=re.IGNORECASE)

    preambulo_end = min(
        index
        for index in (
            recebi_match.start() if recebi_match else len(value),
            data_start,
            final_match.start() if final_match else len(value),
            len(value),
        )
    )

    corpo_start = recebi_match.start() if recebi_match else preambulo_end
    corpo_end = final_match.start() if final_match else data_start
    if corpo_end < corpo_start:
        corpo_end = corpo_start

    final_start = final_match.start() if final_match else data_start
    final_end = data_start
    if final_end < final_start:
        final_end = final_start

    assinatura_start = data_end
    assinatura_end = len(value)
    if assinatura_start > assinatura_end:
        assinatura_start = assinatura_end

    sections = {
        "preambulo": _section("preambulo", value, 0, preambulo_end),
        "corpo": _section("corpo", value, corpo_start, corpo_end),
        "paragrafo_final": _section("paragrafo_final", value, final_start, final_end),
        "data": _section("data", value, data_start, data_end),
        "assinaturas": _section("assinaturas", value, assinatura_start, assinatura_end),
    }
    return DocumentSections(text=value, sections=sections)


def _section(name: str, text: str, start: int, end: int) -> TextSection:
    safe_start = max(0, min(len(text), start))
    safe_end = max(safe_start, min(len(text), end))
    return TextSection(name, text[safe_start:safe_end].strip(), safe_start, safe_end)


def _last_match(pattern: re.Pattern[str], text: str) -> re.Match[str] | None:
    matches = list(pattern.finditer(text))
    return matches[-1] if matches else None
