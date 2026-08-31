# DOCFILL PRO - Auditoria Conservadora

Data: 12/06/2026

## O que foi verificado

- Preview do documento com atualização por debounce, sem reprocessar o template a cada tecla.
- Substituição de marcadores em parágrafos, tabelas, cabeçalhos e rodapés.
- Geração de `.docx` sem modificar o template original.
- Preservação de estrutura do Word: tabelas, cabeçalhos, rodapés, mídia/logo e runs de assinatura.
- Nome de arquivo gerado com caracteres seguros para Windows.
- Bloqueio de geração quando Comprador, CPF/CNPJ ou Vendedor estão vazios.
- Tratamento de template ausente, pasta de saída ausente e DOCX inválido.
- Prioridade dos campos principais sobre marcadores salvos no JSON.
- Fechamento da UI com cancelamento de atualização de preview pendente.
- Prontidão básica para PyInstaller, especialmente dados graváveis fora do bundle.

## O que foi corrigido

- `services/docx_writer.py`
  - Adicionada proteção para impedir que o arquivo gerado sobrescreva o template original.
  - Substituição de marcadores passou a atuar por faixa de texto nos runs, sem usar `paragraph.text` como fallback destrutivo.
  - Marcadores divididos entre runs agora são substituídos preservando melhor a formatação e objetos do parágrafo.

- `ui/main_window.py`
  - Adicionado fechamento limpo com `close_app`, cancelando callback pendente de preview antes de destruir a janela.
  - Mantida referência da imagem do logo carregada na interface.
  - Saneamento de nome de arquivo reforçado para caracteres inválidos do Windows e espaços/pontos finais.

- `services/mapping_manager.py`
  - Em execução empacotada, o JSON de mapeamentos passa a usar `%LOCALAPPDATA%/DocFillPro/data/mappings.json`, evitando gravação dentro do bundle do PyInstaller.

## Testes rodados

- `python -m compileall .`
  - O comando literal falhou porque o alias global `python` não está disponível neste Windows.
- `..\.venv\Scripts\python.exe -m compileall .`
  - Compilação concluída com sucesso no ambiente virtual real do app.
- Teste funcional real com criação de template `.docx`.
- Geração de documento `.docx` real a partir do template temporário.
- Verificação de substituição em:
  - parágrafos;
  - tabela no corpo;
  - cabeçalho;
  - rodapé;
  - tabela no rodapé.
- Verificação de marcador dividido entre runs.
- Verificação de preservação de logo/mídia no arquivo gerado.
- Verificação de preservação de tabela e formatação de assinatura.
- Verificação de hash do template antes e depois da geração.
- Verificação de bloqueio contra sobrescrita do template original.
- Verificação de nome seguro para Windows.
- Verificação de prioridade dos campos principais sobre mapeamentos JSON.
- Verificação de erro para template ausente e DOCX inválido.
- Verificação de fechamento da UI com preview agendado.

## Limitações que permanecem

- A biblioteca `python-docx` não cobre de forma completa conteúdos em caixas de texto, SmartArt, comentários, notas de rodapé/fim e alguns objetos avançados do Word.
- Quando um marcador atravessa vários runs com formatações diferentes, o texto substituído assume a formatação do primeiro run do marcador.
- Para empacotar com PyInstaller, o logo precisa ser incluído como dado do bundle, por exemplo com `--add-data "assets/logo.png;assets"`.
- O app trata DOCX inválido com mensagem de erro genérica da interface; a falha é bloqueada, mas a mensagem ainda pode ser refinada futuramente.
