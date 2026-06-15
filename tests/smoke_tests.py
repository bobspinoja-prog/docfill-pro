from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import customtkinter as ctk
from docx import Document

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.docx_reader import DOCXReader
from services.docx_writer import DOCXWriter
from services.mapping_manager import MappingManager
from ui.main_window import DocFillProApp


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_marker_docx_roundtrip() -> None:
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        template = tmp_path / "template.docx"
        output = tmp_path / "output.docx"

        doc = Document()
        doc.add_paragraph("Comprador: {{COMPRADOR}}")
        table = doc.add_table(rows=1, cols=2)
        table.cell(0, 0).text = "CPF"
        table.cell(0, 1).text = "{{CPF_CNPJ}}"
        section = doc.sections[0]
        section.header.paragraphs[0].text = "Cidade {{CIDADE}}"
        section.footer.paragraphs[0].text = "Data {{DATA}}"
        doc.save(template)

        replacements = {
            "{{COMPRADOR}}": "Cliente Teste",
            "{{CPF_CNPJ}}": "111.222.333-44",
            "{{CIDADE}}": "Campinas",
            "{{DATA}}": "12/06/2026",
        }

        before = file_hash(template)
        DOCXWriter().generate(template, output, replacements)
        assert before == file_hash(template), "template original foi alterado"

        generated_text = DOCXReader(output).extract_text({})
        for value in replacements.values():
            assert value in generated_text
        assert "{{" not in generated_text


def test_marker_split_across_runs_is_replaced() -> None:
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        template = tmp_path / "split.docx"
        output = tmp_path / "split_output.docx"

        doc = Document()
        paragraph = doc.add_paragraph()
        paragraph.add_run("Olá ")
        paragraph.add_run("{{COMPRADOR}}")
        paragraph.add_run("!")
        doc.save(template)

        DOCXWriter().generate(template, output, {"{{COMPRADOR}}": "Cliente Teste"})

        generated_text = DOCXReader(output).extract_text({})

        assert "Cliente Teste" in generated_text
        assert "{{COMPRADOR}}" not in generated_text


def test_repeated_marker_is_fully_replaced() -> None:
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        template = tmp_path / "repeated.docx"
        output = tmp_path / "repeated_output.docx"

        doc = Document()
        doc.add_paragraph(" ".join(["{{COMPRADOR}}"] * 12))
        doc.save(template)

        DOCXWriter().generate(template, output, {"{{COMPRADOR}}": "Cliente"})

        generated_text = DOCXReader(output).extract_text({})

        assert generated_text.count("Cliente") == 12
        assert "{{COMPRADOR}}" not in generated_text


def test_mapping_priority_and_filename() -> None:
    with TemporaryDirectory() as tmp:
        mapping = MappingManager(Path(tmp) / "mappings.json")
        mapping.add_marker("{{COMPRADOR}}", "Custom")
        replacements = mapping.build_replacements({"{{COMPRADOR}}": "Principal"})
        assert replacements["{{COMPRADOR}}"] == "Principal"

    safe_name = DocFillProApp._sanitize_filename('Maria: Silva / Teste?* .')
    assert safe_name
    assert not any(char in safe_name for char in '<>:"/\\|?*')
    assert not safe_name.endswith((".", " "))


def test_ui_layout() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")
    app = DocFillProApp()
    app.geometry("1366x768")
    app.update()
    assert len(app.form_panel.entries) == 11
    assert app.form_panel.winfo_width() >= 420
    assert app.preview_panel.winfo_width() >= 600
    app.close_app()


def test_example_document_if_available() -> None:
    downloads = Path.home() / "Downloads"
    examples = [
        path
        for path in downloads.glob("*.docx")
        if "exemplo app" in path.name and not path.name.startswith("~$")
    ]
    if not examples:
        print("example docx not found; skipping example-specific smoke test")
        return

    template = examples[0]
    reader = DOCXReader(template)
    suggestions = reader.suggest_values()
    if not {"{{COMPRADOR}}", "{{CPF_CNPJ}}", "{{VENDEDOR}}"}.issubset(suggestions):
        print(f"example docx {template.name} is not the expected fixture; skipping example-specific smoke test")
        return

    assert suggestions["{{COMPRADOR}}"].startswith("ANDERSON")
    assert suggestions["{{CPF_CNPJ}}"] == "269.199.688-35"
    assert suggestions["{{VENDEDOR}}"].startswith("RODRIGO")

    values = {
        "{{COMPRADOR}}": "CLIENTE TESTE DOCFILL",
        "{{NACIONALIDADE}}": "brasileira",
        "{{PROFISSAO}}": "engenheira",
        "{{ESTADO_CIVIL}}": "solteira",
        "{{CPF_CNPJ}}": "111.222.333-44",
        "{{LOTE}}": "99",
        "{{QUADRA}}": "10A",
        "{{EMPREENDIMENTO}}": "LOTEAMENTO TESTE VERDE",
        "{{VENDEDOR}}": "VENDEDOR TESTE DOCFILL",
        "{{CIDADE}}": "Campinas",
        "{{DATA}}": "12 de Junho de 2026",
    }
    replacements = MappingManager(ROOT / "data" / "mappings.json").build_replacements(values)
    replacements.update(reader.build_literal_replacements(values))

    output_dir = ROOT / "test_outputs"
    output_dir.mkdir(exist_ok=True)
    output = output_dir / "SMOKE_TEST_EXEMPLO.docx"
    if output.exists():
        output.unlink()

    before = file_hash(template)
    DOCXWriter().generate(template, output, replacements)
    assert before == file_hash(template), "template exemplo foi alterado"

    generated_text = DOCXReader(output).extract_text({})
    for expected in (
        "CLIENTE TESTE DOCFILL",
        "111.222.333-44",
        "Lote 99",
        "Quadra 10A",
        "LOTEAMENTO TESTE VERDE",
        "VENDEDOR TESTE DOCFILL",
        "Campinas, 12 de Junho de 2026",
    ):
        assert expected in generated_text


def main() -> None:
    tests = [
        test_marker_docx_roundtrip,
        test_marker_split_across_runs_is_replaced,
        test_repeated_marker_is_fully_replaced,
        test_mapping_priority_and_filename,
        test_ui_layout,
        test_example_document_if_available,
    ]
    for test in tests:
        test()
        print(f"ok - {test.__name__}")


if __name__ == "__main__":
    main()
