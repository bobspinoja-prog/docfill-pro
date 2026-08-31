# AUDIT_REPORT - Extracao Inteligente DOCFILL PRO

Data: 2026-06-18

## Campos detectados

| Campo | Valor | Fonte | Confianca | Motivo |
| --- | --- | --- | --- | --- |
| COMPRADOR |  | not_found | 0.00 |  |
| NACIONALIDADE |  | not_found | 0.00 |  |
| PROFISSAO |  | not_found | 0.00 |  |
| ESTADO_CIVIL |  | not_found | 0.00 |  |
| CPF_CNPJ | 436.106.638-80 | fallback | 0.90 | padrao de CPF/CNPJ sem rotulo |
| LOTE |  | not_found | 0.00 |  |
| QUADRA |  | not_found | 0.00 |  |
| EMPREENDIMENTO |  | not_found | 0.00 |  |
| VENDEDOR | CARLOS ALBERTO CHAIN CAMPANA | preambulo | 0.94 | nome apos gatilho de aquisicao; conflito no paragrafo final |
| CIDADE |  | not_found | 0.00 |  |
| DATA |  | not_found | 0.00 |  |

## Conflitos encontrados

- VENDEDOR: 'JOAO FINAL ERRADO. R' em paragrafo_final ignorado para preservar 'CARLOS ALBERTO CHAIN CAMPANA'. Motivo: nome conflitante em paragrafo final.

## Fontes por secao

- preambulo: 337 caracteres
- corpo: 18 caracteres
- paragrafo_final: 203 caracteres
- data: 0 caracteres
- assinaturas: 0 caracteres

## Limitacoes restantes

- A extracao prioriza preambulo estruturado; documentos fora do molde podem gerar baixa confianca.
- Assinaturas sao usadas para confirmacao/fallback, mas nao substituem campos do preambulo quando houver conflito.
- Paragrafo final e corpo permanecem limitados a fallback de baixa confianca para evitar falsos positivos.
