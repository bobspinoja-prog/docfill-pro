# DocFill Pro

**[Português](README.pt-BR.md) | English**

A Windows desktop app that fills Word (`.docx`) and PDF contract templates automatically. Point it at a real-estate purchase declaration, and it reads the document, finds buyer, seller, CPF/CNPJ, lot, block, development name, city and date on its own, shows you a live A4 preview, and generates a filled copy — without ever touching the original template.

![DocFill Pro screenshot](docs/screenshots/app-preview.png)

## Why this exists

A small real-estate back office was filling the same declaration template by hand for every new buyer: copy a name here, a CPF there, retype the lot/block/development, then read the whole thing again to catch typos. DocFill Pro replaces that with a form, a live preview, and a field-detection engine that already knows what a filled contract of this shape looks like.

## What it does

- **Reads `.docx` and `.pdf` templates** — extracts paragraphs, tables, headers/footers (DOCX) or text blocks per page (PDF, via PyMuPDF).
- **Detects fields automatically** from natural legal Portuguese (e.g. *"portador do CPF nº ..., na qualidade de COMPRADOR do Lote ... Quadra ... do LOTEAMENTO ..."*), with a confidence score and the exact snippet it matched, so a low-confidence guess is never silently trusted.
- **Marks placeholders on existing text** (`{{COMPRADOR}}`, `{{CPF_CNPJ}}`, ...) and safely replaces only the exact, unambiguous occurrences of a detected value — it refuses to replace a value that appears more than once with different meanings.
- **Live A4 preview** with marker highlighting, zoom, and page/word/character counts; for PDFs, a rendered page view where you can drag-select an area and manually map it to a field.
- **Per-template learning**: every template is hashed, and corrections you make are remembered next time you load that same file.
- **History-based suggestions**: once you type a buyer or seller name, it looks through previously generated documents for the same person and offers to fill in the rest (nationality, profession, city, ...), scored by name-similarity, not just an exact match.
- **Autosave & session restore**: the in-progress form, template and output folder are saved automatically and offered back on next launch.
- **Multi-language UI**: Portuguese, English and Chinese.

## Tech stack

Python 3.11+, [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the UI, [python-docx](https://python-docx.readthedocs.io/) for Word documents, [PyMuPDF](https://pymupdf.readthedocs.io/) for PDF rendering/editing, Pillow for image handling, PyInstaller + Inno Setup for the Windows installer.

## Getting started

```bash
git clone https://github.com/bobspinoja-prog/docfill-pro.git
cd docfill-pro
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python main.py
```

Runtime data (history, learned templates, autosave) is stored per-user under `%LOCALAPPDATA%\DocFillPro`, seeded from the empty defaults in `data/` on first run — running from source never writes into the repo.

### Running the tests

```bash
pip install pytest
pytest -q
```

### Building the Windows installer

```bash
pip install -r requirements-build.txt
pyinstaller "DOCFILL PRO.spec"
# then compile installer/DocFillPro.iss with Inno Setup
```

## Project structure

```
main.py                      entry point
services/                    extraction, PDF/DOCX generation, persistence — no UI code
  field_extractor.py          regex-based field detection engine
  text_sections.py            splits a document into preamble/body/closing/signatures
  template_semantic_analyzer.py  per-field detection + confidence, learns per template hash
  semantic_replacements.py    decides which detected values are safe to auto-replace
  docx_reader.py / docx_writer.py   DOCX preview extraction / marker replacement
  pdf_handler.py              PDF text extraction, rendering, and in-place filling
  history_manager.py / history_suggestions.py   past-document store and cross-document suggestions
  runtime_json_store.py       small JSON store with atomic writes, mtime caching, and bundle seeding
ui/                           CustomTkinter widgets
  main_window.py               app shell + orchestration (template loading, generation, autosave)
  settings_window.py / history_window.py / about_window.py   self-contained dialogs
  pdf_area_dialog.py           modal for mapping a dragged PDF area to a field
  form_panel.py / preview_panel.py   the two main panels
tests/                        pytest suite
data/                         empty-by-default seed files copied on first run
```

## How field detection works

A document is split into sections (preamble, body, closing paragraph, signature block) using known anchor phrases (`RECEBI`, `Assim, por todo o exposto`, a trailing "*city*, *date*" line). Each field is then matched against a section with a pattern specific to where that field actually appears in this type of declaration — for example, the seller's name is looked for right after an acquisition clause in the preamble, confirmed again in the signature block, and flagged as a conflict if the closing paragraph names someone else. A second, lower-confidence fallback pass covers phrasing the structured pass misses (buyer name not at the very start of the preamble, a lot/block mentioned without the full "na qualidade de COMPRADOR do Lote..." context, ...). Every detected value carries a confidence score and the snippet that produced it, and only values above a threshold are used to safely rewrite the original document with `{{MARKERS}}`.

## Known limitations

This was purpose-built around one family of Brazilian real-estate purchase declarations — the fixed 11-field form and the detection heuristics both assume that shape of document, so accuracy drops fast on a differently worded contract. `field_extractor.py` is the single detection engine (it used to be duplicated with `template_semantic_analyzer.py`); generalizing it to other document shapes would mean making the section anchors and structured patterns configurable rather than hardcoded.

## License

[MIT](LICENSE)
