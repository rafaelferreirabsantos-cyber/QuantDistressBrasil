# Sprint 02 — Cobertura e parecer de prontidão

ImpactUFSCar — Área de Pesquisa & Mercado. Análise das capturas oficiais de DFP, FCA e cadastro de companhias obtidas em 20 de novembro de 2026. O painel divide os resultados em sete partições anuais, de 2019 a 2025. Parquet e CSV de execução permanecem locais.

## Universo e elegibilidade

- A unidade do cadastro combina CNPJ, código CVM e data de referência da DFP. O universo inclui as referências observadas no índice de entregas, com linhas distintas em `con` e `ind`, inclusive quando um escopo carece de demonstrações. Conserva a versão máxima do índice, com bloqueio analítico se houver empate de entregas nessa versão. Chaves incompletas ou inválidas são registradas nos totais do manifesto.
- A classificação usa a seção geral do FCA com referência no mesmo ano e até a data de referência da DFP. Aplica a última referência e a maior versão desse FCA disponíveis na captura. A chave exige concordância de código CVM e CNPJ. O vínculo duplicado na versão FCA selecionada deixa a classificação aberta. O painel mantém o rótulo de setor da fonte, o número e versão do documento, sua data de referência, data de recebimento quando vinculada, e arquivo e linha de origem. O rótulo de setor é mapeado por lista explícita. O setor principal declarado orienta a classificação das holdings. Holdings sem setor principal, seguradoras, securitizadoras e bolsas exigem leitura específica. [FCA](https://dados.cvm.gov.br/dataset/cia_aberta-doc-fca) · [Regras de classificação](../src/quantdistress/data/universe.py)
- O cadastro atual serve apenas ao diagnóstico cadastral, inclusive cancelamentos posteriores à referência. Inscrições canceladas, suspensas ou inativas permanecem no universo se constarem no índice. Conflitos cadastrais ficam identificados. O universo documental cobre emissores observados na DFP e deixa em aberto a população que deixou de entregar ou nunca consta do índice. A FCA desta captura também pode refletir reapresentações. [Cadastro oficial](https://dados.cvm.gov.br/dataset/cia_aberta-cad) · [Limitações temporais](historico-dfp.md)

| Ano | Referências DFP | Não financeiras | Financeiras | Regime específico | Sem classificação | Com cancelamento posterior |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2019 | 671 | 443 | 43 | 108 | 77 | 180 |
| 2020 | 733 | 501 | 42 | 107 | 83 | 187 |
| 2021 | 771 | 565 | 46 | 118 | 42 | 187 |
| 2022 | 731 | 579 | 47 | 75 | 30 | 123 |
| 2023 | 733 | 588 | 42 | 63 | 40 | 94 |
| 2024 | 709 | 593 | 40 | 53 | 23 | 57 |
| 2025 | 671 | 577 | 36 | 47 | 11 | 20 |
| Total de referências | **5.019** | **3.846** | **296** | **571** | **306** | **848** |

Cada referência conta uma vez nesta tabela. O mesmo emissor pode aparecer em anos diferentes. Há 499 referências com recebimento do FCA associado posterior à referência da DFP. Há dois empates na versão máxima da entrega DFP, em 2021 e 2023, e um empate no FCA de 2021. Ambos os escopos permanecem no painel. `cobertura_setor.csv` detalha a classificação e a presença de fatos por setor declarado, escopo e ano.

## Cobertura contábil e dos indicadores

O pipeline leu 4.246.513 linhas contábeis, selecionou 4.205.962 para a camada analítica e manteve 168 chaves contábeis conflitantes sem seleção. A seleção usa versões inequivocamente vinculadas e aplica a política de repetição exata antes da extração de insumos. As linhas iniciais e excluídas continuam rastreáveis pelos Parquet intermediários e pela auditoria. [Auditoria de duplicatas de 2024](auditoria-duplicatas.md)

| Protótipo | 2019–25 `con` | 2019–25 `ind` | 2024 `con` | 2024 `ind` |
| --- | ---: | ---: | ---: | ---: |
| Margem operacional | 2.582 | 2.987 | 408 | 464 |
| Rentabilidade operacional sobre ativos | 2.624 | 3.788 | 413 | 586 |
| Caixa operacional sobre receita | 2.583 | 2.988 | 408 | 464 |
| Giro do ativo | 2.621 | 3.772 | 412 | 583 |
| Crescimento da receita | 2.537 | 2.952 | 405 | 456 |
| Liquidez corrente | 2.635 | 3.828 | 412 | 587 |
| Patrimônio líquido sobre ativo | 2.635 | 3.819 | 412 | 586 |
| Financiamentos reportados sobre ativo | 2.635 | 3.817 | 412 | 586 |
| Financiamentos circulantes sobre caixa | 2.614 | 3.733 | 409 | 575 |

Os valores são contagens válidas. O denominador não financeiro é de 3.846 referências por escopo para 2019–25 e 593 em 2024, inclusive referências sem fatos naquele escopo. De 90.342 linhas de saída dos nove protótipos e dois escopos, 55.150 têm valor válido. Entre as linhas não financeiras, as causas mais frequentes de indisponibilidade são ausência de fatos no escopo (10.917), denominador inválido (2.842) e período incompatível (246). A contagem atribui a primeira situação impeditiva de cada cálculo. O CSV de indicadores disponibiliza essas situações por indicador, setor declarado, escopo e ano. [Fórmulas e regras](conceitos-indicadores.md)

## Parecer para a Sprint 03

O painel está apto para exploração contábil descritiva e revisão dos protótipos. Nove medidas têm cálculo e linhagem reproduzíveis com regras explícitas. A aptidão para validação prospectiva continua condicionada à recuperação das versões históricas e da evidência de quando os valores se tornaram públicos. Os ZIPs anuais observados preservam metadados de entregas anteriores, enquanto seus fatos correspondem à versão máxima. A aprovação metodológica cabe à Área de Pesquisa & Mercado.

| Decisão pendente | Evidência para a revisão |
| --- | --- |
| Constituir base temporal e universo de diligência | Reconciliar versões documentais com contas e datas de divulgação verificáveis. Ampliar o universo histórico e medir exclusões por saída ou falta de entrega. |
| Tratar conflitos contábeis e validar a taxonomia do FCA | Conferir casos no formulário oficial e revisar a adequação de cada grupo, especialmente holdings individuais e regimes específicos. |
| Validar sinais, comparabilidade e cobertura mínima | Fixar elegibilidade e tratamentos por setor. Rever denominadores próximos de zero, extremos, exercícios irregulares e diferenças entre métodos de DFC. |
| Ampliar as dimensões candidatas | Diligenciar dívida onerosa, juros brutos, capital empregado e estabilidade. Verificar cobertura antes de discutir pesos ou escalas dos dois índices. |
| Planejar avaliação fora da amostra | Revisar eventos públicos datados, horizonte, regras de censura e protocolo temporal antes de qualquer avaliação de associação prospectiva. |
