# Auditoria das chaves contábeis repetidas

A análise usa o Parquet de fatos da captura DFP 2024 identificada pelo SHA-256 `0a1e41edc81900df6605448acb2fcf6fae36f9a8ac4756a7d658cd7c718a1501`. Uma chave contábil reúne CNPJ, código CVM, data de referência, versão, família, escopo, ordem, início e fim do exercício e código de conta. O início do exercício pode ficar vazio em BPA e BPP, que são demonstrações de saldo. [Dicionário da ingestão](dicionario-dados.md) · [Cobertura da captura de 2024](cobertura-dfp-2024.md)

## Classificação e seleção

O diagnóstico recalcula as chaves repetidas a partir de todos os fatos. Compara os campos preservados do CSV e os metadados disponíveis de vínculo e escala. Se os campos coincidirem depois da ingestão, a seleção também exige que `FATO_REPETIDO` confirme a repetição na fonte, quando esse campo estiver disponível. A localização física no arquivo distingue as ocorrências e indica qual delas entra na seleção.

| Classe | Critério | Tratamento |
| --- | --- | --- |
| `exata` | Conteúdo e metadados comparados idênticos em todo o grupo. | Para chaves completas, usar um único registro, escolhendo o primeiro por arquivo de origem e posição no arquivo. Para chaves incompletas, manter o grupo pendente. |
| `valor` | Valoração decimal divergente na escala declarada ou diferença entre valor presente e ausente. A comparação usa `Decimal` e preserva a precisão original. | Manter a chave pendente. |
| `rotulo` | Descrições da conta diferentes, mesmo quando o valor coincidir. | Manter a chave pendente. |
| `outros` | Variação em outro campo, como moeda, escala, natureza de conta fixa, metadados de vínculo ou grafia decimal de um mesmo número. Inclui a coincidência dos campos após a ingestão sem confirmação da repetição pelo indicador da fonte. | Manter a chave pendente. |
| `mista` | Mais de um tipo de divergência no mesmo grupo. | Manter a chave pendente e registrar cada tipo nos indicadores booleanos. |

A seleção de fatos retém as chaves únicas e um representante de cada grupo exato de chave completa. A seleção depende do conteúdo do grupo e da linhagem, independentemente da ordem do DataFrame. Um grupo com valores concorrentes exige revisão do documento e da hierarquia contábil para orientar qualquer seleção posterior. Somar ou calcular a média de linhas concorrentes criaria um valor com interpretação própria, sem correspondência comprovada no formulário. As regras posteriores de elegibilidade ainda precisam validar escopo, vínculo documental, período e conceito da conta. Uma chave única incompleta permanece disponível para esses controles.

## Resultado da DFP 2024

As 7.270 linhas sinalizadas na ingestão pertencem a 3.300 chaves repetidas. O diagnóstico reproduziu esse total e a sinalização original de repetições exatas.

| Classe | Chaves | Linhas | Registros na seleção |
| --- | ---: | ---: | ---: |
| Exata | 3.283 | 7.236 | 3.283 |
| Divergência de valor | 5 | 10 | 0 |
| Divergência de rótulo | 12 | 24 | 0 |
| Outros campos ou divergências mistas | 0 | 0 | 0 |
| **Total** | **3.300** | **7.270** | **3.283** |

Os 17 grupos pendentes pertencem ao escopo individual e concentram-se em um emissor. As divergências de valor atingem dois grupos de BPP e três de DFC indireta, todos do último exercício. As divergências de rótulo atingem quatro grupos de BPA, quatro de BPP e quatro de DFC indireta, metade do último exercício e metade do comparativo. Por exemplo, o código `2.01.04.03.01` tem os rótulos “Arrendamento Mercantil a Pagar” e “Passivo de Arrendamento” dentro de uma mesma chave. A coincidência de valor deixa a interpretação do código em aberto.

A seleção retorna **619.659 dos 623.646 fatos**. A redução de 3.987 linhas corresponde a 3.953 cópias excedentes e 34 linhas de chaves pendentes. Todos os fatos originais continuam disponíveis para reprocessamento e cada ocorrência repetida permanece identificável na trilha de auditoria.

## Reprodução

Execute o trecho abaixo com o Parquet da captura indicada, a partir da raiz do repositório. No painel com vários anos, aplique a função a cada captura antes de juntar as saídas e mantenha o SHA-256 em todas as tabelas combinadas.

```python
from pathlib import Path

import pandas as pd

from quantdistress.evaluation.duplicates import auditar_duplicatas

sha = "0a1e41edc81900df6605448acb2fcf6fae36f9a8ac4756a7d658cd7c718a1501"
captura = Path("data/interim/dfp/2024") / sha
auditoria = auditar_duplicatas(pd.read_parquet(captura / "fatos.parquet"))
resumo = auditoria.grupos_repetidos.groupby("CLASSE_DUPLICATA").agg(
    CHAVES=("N_LINHAS", "size"), LINHAS=("N_LINHAS", "sum")
)
print(resumo)
```

O resultado expõe `fatos_selecionados`, `grupos_repetidos`, `linhas_repetidas` e `chaves_nao_resolvidas`. As duas tabelas de auditoria registram os campos que divergiram e a origem escolhida, quando aplicável. A tabela de linhas conserva os dados da fonte, incluindo `ARQUIVO_ORIGEM` e `LINHA_ORIGEM`, além de marcar a ocorrência selecionada com `SELECIONADA_ANALITICA`.
