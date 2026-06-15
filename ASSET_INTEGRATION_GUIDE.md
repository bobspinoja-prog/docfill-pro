# 📋 Guia de Integração de Assets

## Passo 1: Salvar as Imagens

Salve os dois arquivos PNG no diretório `assets/`:

```
c:\Users\estagiario1\Nova pasta\DocFillPro\assets\
├── ICON_EXTERNAL.png       ← Ícone externo (salve aqui)
├── SYMBOL_INTERNAL.png     ← Símbolo interno (salve aqui)
├── app_icon.ico
└── logo.png
```

## Passo 2: Processar Assets

Execute o script de processamento:

```bash
cd "c:\Users\estagiario1\Nova pasta\DocFillPro"
.\.venv\Scripts\python.exe scripts/process_assets.py
```

Isso irá gerar:

```
assets/icons/
├── docfill.ico                          # Ícone com múltiplas resoluções
├── docfill_16x16.png
├── docfill_32x32.png
├── docfill_48x48.png
├── docfill_64x64.png
├── docfill_128x128.png
├── docfill_256x256.png
├── docfill_512x512.png
├── symbol_sidebar_32x32.png
├── symbol_header_20x20.png
├── symbol_empty_96x96.png
├── symbol_loading_48x48.png
└── symbol_original.png
```

## Passo 3: Validar Integração

- Verificar que os ícones estão nos diretórios corretos
- Executar a aplicação e validar a interface
- Testar em tema claro e escuro
- Verificar escala em 100%, 125% e 150%

## Arquivos Modificados

- `ui/main_window.py` - Símbolo interno na sidebar e empty states
- `ui/preview_panel.py` - Símbolo em states vazios
- `ui/form_panel.py` - Símbolo em loading
- `DOCFILL PRO.spec` - Configuração de ícone atualizada
- `installer/DOCFILL_PRO_Inno.iss` - Referência ao novo ícone

## Relatório de Integração

Execute após o Passo 2 para gerar relatório completo:

```bash
.\.venv\Scripts\python.exe scripts/integration_report.py
```
