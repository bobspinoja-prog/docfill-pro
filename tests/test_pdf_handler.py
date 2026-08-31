import os
from pathlib import Path

import pytest

fitz = pytest.importorskip("fitz")

import customtkinter as ctk

from services.pdf_handler import PDFHandler, PDFManualArea
from ui.main_window import DocFillProApp


PDF_PREAMBLE = (
    "DECLARAÇÃO RENAN SARTOR PIESTCH, brasileiro, empresário, casado, "
    "portador do CPF n° 058.8836.619-63 na qualidade de COMPRADOR do Lote 20 "
    "Quadra 5A do LOTEAMENTO ALPHAVILLE RIBEIRÃO PRETO, vendido atraves do "
    "contrato de compra e venda de sobre imóvel com permuta do(a) ROBERTO "
    "PADUA VALADAO JUNIOR para os devidos fins. Ribeirão Preto, 23 de Junho de 2026"
)


def _make_pdf(path: Path, text: str = PDF_PREAMBLE) -> None:
    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_textbox(fitz.Rect(56, 92, 540, 220), text, fontsize=10, fontname="helv")
    document.save(path)
    document.close()


def test_pdf_handler_detects_fields_and_renders_pages(tmp_path: Path) -> None:
    pdf_path = tmp_path / "declaracao.pdf"
    _make_pdf(pdf_path)

    handler = PDFHandler(pdf_path)
    detections = handler.detect_fields()
    pages = handler.render_pages(100)

    assert detections["{{COMPRADOR}}"].value == "RENAN SARTOR PIESTCH"
    assert detections["{{CIDADE}}"].value == "Ribeirão Preto"
    assert len(pages) == 1
    assert pages[0].image.width > 0
    assert pages[0].blocks


def test_pdf_handler_generates_filled_pdf_without_touching_original(tmp_path: Path) -> None:
    pdf_path = tmp_path / "declaracao.pdf"
    output_path = tmp_path / "saida.pdf"
    _make_pdf(pdf_path)

    original_size = pdf_path.stat().st_size
    handler = PDFHandler(pdf_path)
    detections = handler.detect_fields()
    values = {marker: detection.value for marker, detection in detections.items()}
    values["{{COMPRADOR}}"] = "CLIENTE PDF TESTE"
    area = PDFManualArea("{{DATA}}", 0, (250, 190, 390, 208), "23 de Junho de 2026")

    report = handler.generate_filled_pdf(
        output_path,
        values,
        manual_areas={"{{DATA}}": [area]},
        detections=detections,
    )

    assert output_path.exists()
    assert pdf_path.stat().st_size == original_size
    assert "{{DATA}}" not in report.skipped
    output_text = "\n".join(page.get_text("text") for page in fitz.open(output_path))
    assert "CLIENTE PDF TESTE" in output_text


def _find_button(widget, text: str):
    for child in widget.winfo_children():
        if isinstance(child, ctk.CTkButton) and child.cget("text") == text:
            return child
        found = _find_button(child, text)
        if found is not None:
            return found
    return None


def test_pdf_area_dialog_saves_manual_area(tmp_path: Path) -> None:
    os.environ["PYTEST_CURRENT_TEST"] = "1"
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")

    pdf_path = tmp_path / "declaracao.pdf"
    _make_pdf(pdf_path)

    app = DocFillProApp()
    try:
        app.load_template(pdf_path, show_errors=False)
        app.update()
        assert app.pdf_area_mappings == {}

        app.handle_pdf_area_selected(0, (10.0, 10.0, 100.0, 30.0), "algum texto")
        app.update()

        dialogs = [w for w in app.winfo_children() if isinstance(w, ctk.CTkToplevel) and w.winfo_exists()]
        assert dialogs, "PDF area dialog did not open"
        dialog = dialogs[-1]

        from ui.i18n import t

        save_button = _find_button(dialog, t("pdf_area_save_button"))
        assert save_button is not None, "save button not found in PDF area dialog"
        save_button.cget("command")()
        app.update()

        assert "{{COMPRADOR}}" in app.pdf_area_mappings
        areas = app.pdf_area_mappings["{{COMPRADOR}}"]
        assert len(areas) == 1
        assert areas[0].rect == (10.0, 10.0, 100.0, 30.0)
        assert not dialog.winfo_exists()
    finally:
        app.close_app()
