# PRE_RELEASE_CHECK - DOCFILL PRO 1.3.0

Data: 2026-06-18

## Testes executados

- `python -m compileall .`
  - Resultado: aprovado.
  - Observacao: sem erro de sintaxe ou import durante compilacao.

- `.venv\Scripts\python.exe -m pytest -v`
  - Resultado: aprovado.
  - Total: 28 testes aprovados.

## Validacoes cobertas

- Geracao DOCX: coberta pelos testes de roundtrip e substituicao de marcadores.
- Preview: coberto por testes de layout/UI e smoke suite.
- Extracao inteligente: coberta por `tests/test_field_extractor.py`.
- Confianca por campo: coberta por validacoes de payload, fonte, razao e ocorrencias.
- Reescrita de template: coberta por `test_rewrite_template_with_markers_preserves_original_and_marks_safe_values`.
- Identificacao contextual: comprador, vendedor, CPF/CNPJ, lote, quadra, empreendimento, cidade e data cobertos pelos testes.
- Conflito de vendedor no paragrafo final: coberto por teste dedicado.

## Erros encontrados

- Smoke funcional inicial encontrou falha de extracao quando caracteres acentuados vinham degradados como `?`, exemplo `RIBEIR?O` e `n?`.

## Correcoes aplicadas

- Incremento de versao do installer para `1.3.0`.
- Installer ajustado para instalacao sem admin em `%LOCALAPPDATA%\Programs\DocFillPro`.
- Dados do usuario preservados em `%LOCALAPPDATA%\DocFillPro`.
- Regex de secionamento/extracao endurecida para tolerar caracteres acentuados degradados como `?`.
- Adicionado teste para preambulo com acentos degradados por OCR/encoding.

## Resultado

Liberado para build PyInstaller e compilacao do installer.
