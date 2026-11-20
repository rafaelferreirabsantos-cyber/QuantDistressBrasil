# Dicionário de dados da DFP

Uma captura é uma cópia do ZIP anual identificada pelo SHA-256 de seus bytes. Esta camada intermediária cobre o índice de entregas e cinco famílias de demonstrações, com dez arquivos contábeis entre os escopos `con` e `ind`. Os CSVs são lidos em Latin-1 com separador `;`. As colunas da CVM mantêm seus nomes e campos vazios se tornam nulos. [Portal DFP](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp) · [Dicionário oficial](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp/resource/cbf44db1-06b8-45f7-8318-88d1564e9451)

## Grão e vínculos

| Artefato | Grão | Chave de trabalho |
| --- | --- | --- |
| ZIP em `data/raw/dfp/<ano>/<sha256>/` | Captura anual do arquivo CVM, com dados da coleta em `origem.json` | SHA-256 dos bytes do ZIP |
| `entregas.parquet` | Um registro do índice de entregas | `CNPJ_CIA`, `CD_CVM`, `DT_REFER`, `VERSAO` para vínculo. Pode se repetir. |
| `fatos.parquet` | Um registro de conta por demonstração e exercício informado | Chave de vínculo mais `FAMILIA`, `ESCOPO`, `ORDEM_EXERC`, `DT_INI_EXERC`, `DT_FIM_EXERC`, `CD_CONTA`. Pode se repetir. |
| `manifesto.json` | Inventário e controle da captura | Ano, versão do esquema, origem do ZIP, inventário dos membros e contagem e hash de cada Parquet |

A identificação física de um registro dentro de uma captura usa `ARQUIVO_ORIGEM` e `LINHA_ORIGEM`. Como duas fontes recém-baixadas podem divergir para o mesmo ano, leve também o SHA-256 da captura para tabelas derivadas e experimentos.

## Colunas comuns

| Coluna | Tipo lógico | Significado |
| --- | --- | --- |
| `CNPJ_CIA` | Texto | CNPJ da companhia conforme CVM, preservando pontuação e zeros iniciais. |
| `CD_CVM` | Texto | Código do emissor na CVM. |
| `DENOM_CIA` | Texto | Nome empresarial conforme o registro de origem. Pode variar ao longo do tempo. |
| `DT_REFER` | Data | Data de referência do formulário. É distinta do fim de cada exercício exibido. |
| `VERSAO` | Inteiro | Versão informada do documento para a companhia e referência. |
| `DT_RECEB` | Data, anulável nos fatos | Data de recebimento informada pela CVM. É uma candidata a aproximação da disponibilidade e requer validação antes do uso em recortes históricos. |
| `ID_DOC` | Texto, anulável nos fatos | Identificador do documento de origem conforme o índice de entregas. |
| `LINK_DOC` | Texto, anulável nos fatos | Endereço informado pela CVM para o formulário específico. |
| `ARQUIVO_ORIGEM` | Texto | Nome do membro CSV do ZIP. |
| `LINHA_ORIGEM` | Inteiro | Posição do registro no CSV, começando em 1 após o cabeçalho. |

## Colunas próprias de `entregas.parquet`

| Coluna | Tipo lógico | Significado |
| --- | --- | --- |
| `CATEG_DOC` | Texto | Categoria do documento informada no índice de entregas. |
| `CHAVE_ENTREGA_REPETIDA` | Booleano | Marca todos os registros cuja chave de vínculo completa aparece mais de uma vez no índice. |

## Colunas próprias de `fatos.parquet`

| Coluna | Tipo lógico | Significado |
| --- | --- | --- |
| `FAMILIA` | Texto | `BPA` (balanço patrimonial ativo), `BPP` (balanço patrimonial passivo), `DRE` (demonstração do resultado), `DFC_MD` (fluxo de caixa pelo método direto), `DFC_MI` (fluxo de caixa pelo método indireto). |
| `ESCOPO` | Texto | `con` para demonstração consolidada, `ind` para individual. |
| `GRUPO_DFP` | Texto | Grupo e denominação da demonstração informados pela CVM. |
| `ORDEM_EXERC` | Texto | Ordem do exercício informada pela CVM. Identifica o exercício corrente e o comparativo no contexto de uma entrega. |
| `DT_INI_EXERC` | Data, anulável | Data inicial do período de fluxo. Fica nula nos balanços, que representam um saldo em uma data. |
| `DT_FIM_EXERC` | Data | Data final do exercício informado ou data do saldo no balanço. |
| `CD_CONTA` | Texto | Código hierárquico da conta. Sua interpretação depende do leiaute, da família e do setor. |
| `DS_CONTA` | Texto | Descrição original da conta. Auxilia a verificação do conceito associado ao código. |
| `ST_CONTA_FIXA` | Texto | Indicador `S` ou `N` de conta fixa na fonte. |
| `MOEDA` | Texto | Rótulo da moeda reportado pela CVM. |
| `ESCALA_MOEDA` | Texto | Rótulo da escala reportada no registro. |
| `VL_CONTA` | Texto decimal, anulável | Valor na representação decimal e escala originais do CSV. A conversão futura para `Decimal` preserva a exatidão para conciliações. |
| `FATOR_ESCALA_MOEDA` | Inteiro, anulável | Fator candidato derivado do rótulo `MIL` (1.000) ou `UNIDADE` (1). Escala desconhecida produz nulo. Verifique a unidade econômica de cada conta antes de aplicar o fator, em especial valores por ação. |
| `SITUACAO_VINCULO` | Texto | `unico` para um vínculo com o índice, `ausente` para nenhum e `ambiguo` para mais de um. Os metadados de entrega dos fatos ficam nulos se o vínculo for ausente ou ambíguo. |
| `CHAVE_REPETIDA` | Booleano | Marca todos os registros que compartilham a chave contábil com outro fato. |
| `FATO_REPETIDO` | Booleano | Marca todos os registros de um grupo de fatos idênticos na origem. |

## Regras de uso na pesquisa

- Use `DT_FIM_EXERC` e `DT_INI_EXERC` para comparar períodos compatíveis. Uma linha comparativa pertence à entrega que a publicou, mesmo quando o seu exercício termina no ano anterior.
- Preserve `ESCOPO` em todas as chaves analíticas. Analise as duas variantes de DFC separadamente até definir as regras de equivalência.
- Diferencie zero reportado, ausência de valor e ausência de conta. Antes de construir indicadores, documente o tratamento de chaves repetidas, ambiguidades, moedas, escalas, contas por ação e diferenças setoriais.
- Para análises históricas, valide a disponibilidade efetiva de cada entrega e o histórico de versões. Quando o vínculo com a entrega estiver ausente ou ambíguo, o fato requer revisão antes de ser elegível para um corte temporal.
