# Resumo Tecnico - DOCFILL PRO

## Local do projeto

Pasta principal:

`C:\Users\estagiario1\Nova pasta\DocFillPro`

## Objetivo

O DOCFILL PRO e um aplicativo desktop em Python para preencher documentos Word `.docx` a partir de templates. O usuario seleciona um modelo, preenche campos no formulario, visualiza um preview textual e gera um novo documento Word sem alterar o template original.

## Tecnologias

- Python
- CustomTkinter
- Tkinter
- python-docx
- Pillow
- JSON para mapeamentos
- PyInstaller para gerar `.exe`
- Inno Setup para gerar instalador Windows

## Estrutura

- `main.py`: ponto de entrada da aplicacao.
- `ui/theme.py`: cores, fontes e estilos compartilhados.
- `ui/main_window.py`: janela principal, header, status bar, body, footer e integracao com os servicos.
- `ui/preview_panel.py`: painel esquerdo com preview do documento em folha A4.
- `ui/form_panel.py`: painel direito com formulario, cards recolhiveis e botoes de acao.
- `services/docx_reader.py`: leitura, extracao de texto, analise e sugestao de campos do `.docx`.
- `services/docx_writer.py`: geracao do documento final preservando estrutura do Word.
- `services/mapping_manager.py`: persistencia e aplicacao dos mapeamentos em JSON.
- `data/mappings.json`: marcadores adicionais.
- `assets/logo.png`: logo usado dentro da interface.
- `assets/logo.ico`: icone externo usado na janela, executavel, instalador e atalho.
- `installer/DOCFILL_PRO_Inno.iss`: script do instalador Inno Setup.
- `tests/smoke_tests.py`: testes funcionais principais.

## Frontend atual

O frontend foi refatorado para um visual desktop premium escuro, com verde como cor principal.

Principais areas:

- Header compacto com logo, titulo, subtitulo e botoes `Tema`, `Ajustes`, `Sobre`.
- Status bar com indicador verde animado, template ativo e pasta de saida.
- Body dividido em duas colunas:
  - esquerda: preview do documento;
  - direita: formulario de preenchimento.
- Footer compacto com versao e status.

## Preview

Arquivo: `ui/preview_panel.py`

Funcionalidades:

- Toolbar com modelo carregado, zoom e botao atualizar.
- Folha A4 branca centralizada dentro de um container escuro.
- Scroll vertical.
- Estado vazio quando nenhum template foi carregado.
- Marcadores `{{CAMPO}}` destacados no preview com verde e fundo claro.
- Rodape com paginas, palavras, caracteres e quantidade de marcadores.

## Formulario

Arquivo: `ui/form_panel.py`

O formulario usa cards recolhiveis:

- Dados do Comprador
- Dados do Imovel
- Dados do Vendedor
- Dados do Documento
- Acoes

Campos obrigatorios:

- `{{COMPRADOR}}`
- `{{CPF_CNPJ}}`
- `{{VENDEDOR}}`

Se um obrigatorio estiver vazio, o campo recebe borda vermelha e mensagem de erro.

## Marcadores principais

- `{{COMPRADOR}}`
- `{{NACIONALIDADE}}`
- `{{PROFISSAO}}`
- `{{ESTADO_CIVIL}}`
- `{{CPF_CNPJ}}`
- `{{LOTE}}`
- `{{QUADRA}}`
- `{{EMPREENDIMENTO}}`
- `{{VENDEDOR}}`
- `{{CIDADE}}`
- `{{DATA}}`

## Backend preservado

Os arquivos de backend nao foram alterados na ultima refatoracao:

- `services/docx_reader.py`
- `services/docx_writer.py`
- `services/mapping_manager.py`
- `main.py`

## Build e instalador

Executavel gerado:

`dist_onefile\DOCFILL PRO.exe`

Instalador Inno Setup:

`dist_installer\DOCFILL_PRO_Inno_Setup.exe`

Instalacao local:

`C:\Users\estagiario1\AppData\Local\DocFillPro\DOCFILL PRO.exe`

Atalho:

`C:\Users\estagiario1\Desktop\DocFill Pro.lnk`

## Testes recentes

Foram rodados:

- `python -m compileall .`
- `python tests\smoke_tests.py`
- abertura automatica da UI
- captura visual da interface em `test_outputs`

Ultimo commit:

`5c75bcb Refactor frontend to premium desktop layout`
