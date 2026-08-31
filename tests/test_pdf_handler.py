from pathlib import Path

import pytest

fitz = pytest.importorskip("fitz")

from services.pdf_handler import PDFHandler, PDFManualArea


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
