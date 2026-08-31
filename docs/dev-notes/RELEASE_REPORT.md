# DOCFILL PRO - Release Report

Data: 2026-06-18
Versao gerada: 1.3.0

## Arquivos produzidos

- Executavel: `dist\DOCFILL PRO.exe`
  - Tamanho: 32.275.155 bytes (30,78 MB)
  - SHA256: `481C1E285B647F1700880A66E6690A81A0961BDC311BEF50A1110E2F250A0A47`

- Installer: `dist_installer\DOCFILL_PRO_SETUP.exe`
  - Tamanho: 41.117.510 bytes (39,21 MB)
  - SHA256: `8AF830DF8BA7225A8DB18F3561B03648FEFD3622A1E08DCF83686F51F59CE74E`

## Build

- PyInstaller: 6.21.0
- Python: 3.14.4 do ambiente `.venv`
- Modo: onefile
- Console: desativado
- Icone: `assets\icons\docfill.ico`
- Spec: `DOCFILL PRO.spec`
- Resultado: aprovado, arquivo gerado em `dist\DOCFILL PRO.exe`

## Installer

- Inno Setup: 7.0.1-beta
- Script: `installer\DocFillPro.iss`
- Output: `dist_installer\DOCFILL_PRO_SETUP.exe`
- Nome: DOCFILL PRO
- Publisher: DOCFILL PRO
- Versao: 1.3.0
- Instalacao sem admin: `PrivilegesRequired=lowest`
- Pasta de instalacao: `%LOCALAPPDATA%\Programs\DocFillPro`
- Pasta de dados do usuario: `%LOCALAPPDATA%\DocFillPro`
- Executavel instalado: `DOCFILL PRO.exe`
- Atalhos:
  - Menu Iniciar: criado automaticamente
  - Area de Trabalho: opcional, validado com `/TASKS=desktopicon`

## Testes executados

- `.venv\Scripts\python.exe -m compileall .`
  - Resultado: aprovado.

- `.venv\Scripts\python.exe -m pytest -v`
  - Resultado: 28 passed.

- Smoke funcional de servicos
  - Resultado: `smoke_services=passed`.
  - Confirmou extracao contextual, geracao DOCX temporaria, leitura/preview textual e reescrita de template com marcadores.

- Smoke do executavel empacotado
  - Resultado: `exe_smoke=opened`.
  - Confirmou que `dist\DOCFILL PRO.exe` abre sem traceback inicial.

- Compilacao do installer
  - Resultado: aprovado.
  - Comando usado: `ISCC installer\DocFillPro.iss`.

## Checklist de validacao

1. Instala normalmente: aprovado, sem acesso de admin.
2. Cria atalhos: aprovado, Desktop e Menu Iniciar.
3. Abre pelo Menu Iniciar: atalho criado apontando para `%LOCALAPPDATA%\Programs\DocFillPro\DOCFILL PRO.exe`.
4. Abre pelo Desktop: atalho criado apontando para `%LOCALAPPDATA%\Programs\DocFillPro\DOCFILL PRO.exe`.
5. Gera documentos: aprovado por testes automatizados e smoke funcional.
6. Preview funciona: aprovado por testes automatizados e smoke funcional.
7. Extracao funciona: aprovado por testes automatizados e smoke funcional.
8. Reescrita de template funciona: aprovado por testes automatizados e smoke funcional.
9. Desinstala corretamente: aprovado via `unins000.exe /VERYSILENT`.
10. Nao remove dados do usuario: aprovado; marcador em `%LOCALAPPDATA%\DocFillPro` preservado apos desinstalacao.

## Observacoes

- O build inclui assets, icones, arquivos de dados semente e dependencias necessarias no executavel onefile.
- O installer inclui apenas o executavel, assets e sementes de dados, excluindo testes, caches, `__pycache__`, logs temporarios e arquivos de desenvolvimento.
- A release foi reinstalada ao final da validacao para deixar o app disponivel no ambiente local.
