# Sprint 03B — Scores experimentais de qualidade e pressão financeira

ImpactUFSCar — Área de Pesquisa & Mercado. A Sprint 03B aplica a especificação da Sprint 03A ao painel revisto da Sprint 02. O resultado mede posição relativa em uma referência contemporânea do mesmo exercício. O modo de todas as saídas é `descritivo_revisado`. [Especificação dos scores](sprint-03a-especificacao.md) · [Inventário do painel e das versões](historico-dfp.md)

## Benchmark

Cada eixo é a média ponderada dos seus componentes e só fica disponível quando todos os seus próprios componentes passam pelos controles de valor, origem documental e referência. A falta de um componente deixa o respectivo eixo indisponível, com seu peso e seu motivo preservados. O outro eixo tem avaliação independente. Os indicadores brutos conservam suas unidades e sinais. [Conceitos e indicadores financeiros](conceitos-indicadores.md)

| Eixo | Componente central | Direção para normalização | Peso |
| --- | --- | --- | ---: |
| Quality | Rentabilidade operacional sobre ativos médios | Crescente | 1/2 |
| Quality | Fluxo de caixa operacional sobre receita | Crescente | 1/2 |
| Financial Distress | Liquidez corrente | Decrescente | 1/3 |
| Financial Distress | Patrimônio líquido sobre ativos | Decrescente | 1/3 |
| Financial Distress | Financiamentos reportados sobre ativos | Crescente | 1/3 |

A inversão de sinal antecede a normalização de liquidez corrente e patrimônio líquido sobre ativos. Um índice de liquidez menor ou uma razão patrimonial menor eleva o componente de pressão relativa, mantida a referência. Patrimônio líquido negativo preserva seu sinal econômico. Financiamentos reportados compreendem os agregados circulante e não circulante validados na DFP. Sua cobertura pode ser menor que a da dívida onerosa total, cuja mensuração depende de conciliação de subcontas e notas, inclusive debêntures e arrendamentos. [Definições e escolhas contábeis](conceitos-indicadores.md)

Para o indicador já orientado $y$, cada referência admissível reúne $n$ emissores distintos com valor válido e rastreável. O percentil empírico de ponto médio é $100\,[\#(r<y)+\tfrac12\#(r=y)]/n$. Empates têm a mesma posição. A referência exata usa o rótulo FCA original, o mesmo ano de exercício no painel e um único escopo. O código CVM avaliado é excluído antes das verificações. O benchmark exige pelo menos 30 pares e dois valores distintos após a exclusão. [Protocolo de referência da Sprint 03A](sprint-03a-revisao-final.md)

## Unidade, elegibilidade e linhagem

A unidade de saída é o código CVM, o exercício, o escopo e a versão metodológica. CNPJ, data de referência, setor FCA, documento e versão da DFP identificam a origem. A última referência anual é determinada antes dos filtros de validade. Empate documental bloqueia os cálculos da observação. O consolidado é o escopo principal. A série individual tem referência própria e exige ausência comprovada de fatos correntes do consolidado da mesma referência nos intermediários DFP verificados. Um consolidado disponível com componentes inválidos permanece um caso consolidado incompleto. Holdings classificadas no grupo não financeiro e com setor identificável podem participar do consolidado. Holdings individuais exigem protocolo próprio. [Elegibilidade proposta](sprint-03a-especificacao.md#elegibilidade-contábil-e-cobertura) · [Viabilidade por escopo](sprint-03a-viabilidade.md#holdings-e-escopo-individual)

| Dimensão | Evidência preservada |
| --- | --- |
| Disponibilidade dos componentes | Valores brutos finitos, componentes presentes e motivo da indisponibilidade quando houver. A cobertura ponderada usa os pesos fixos da configuração. |
| Suporte estatístico | Tipo e identidade da referência, tamanho após excluir o alvo, dispersão e método. Referências insuficientes ou constantes têm status próprio. |
| Qualidade contábil | Situação e detalhe do indicador, contas e linhas de origem, família da demonstração, escopo, período, unidade, documento, versão e hash do arquivo. Validação automatizada da linhagem e revisão documental independente são etapas distintas. |
| Elegibilidade temporal | Modo descritivo revisado e evidência de divulgação quando registrada. A habilitação histórica depende de verificar a versão e a disponibilidade do alvo e de todos os insumos da referência na data de corte. |

Denominadores inválidos, exercícios incompatíveis, contas ausentes e divergências documentais conservam os motivos da etapa de indicadores. O marcador de caixa zero distingue a presença de financiamento circulante positivo de um financiamento circulante reportado igual a zero, quando os dois saldos estão demonstrados. Se o financiamento permanecer indeterminado, a origem disponível indica a extensão da evidência. A razão de financiamento circulante sobre caixa fica indefinida com denominador zero. Os marcadores diagnósticos permanecem separados dos pesos de Quality e Financial Distress. O suporte descreve as condições do cálculo. Precisão, confiabilidade preditiva e probabilidade de um evento exigem desenho de validação próprio. [Contas, sinais e linhagem](conceitos-indicadores.md#validade-e-rastreabilidade) · [Dimensões de suporte](sprint-03a-especificacao.md#diagnóstico-de-suporte-em-quatro-dimensões)

## Cobertura do benchmark e matriz exploratória

O denominador documental inclui observações indisponíveis para um eixo ou para ambos. A matriz Quality × Financial Distress exige os dois eixos calculados. A cobertura deve ser lida por ano, setor FCA e escopo. Contagens de emissor-ano e contagens de códigos CVM distintos respondem a perguntas diferentes quando um emissor aparece em vários exercícios.

O benchmark `03b.1` processou as sete partições de 2019 a 2025. A saída contém 10.016 observações documentais e 50.080 registros de componentes. São 5.008 observações em cada escopo e 909 códigos CVM distintos no período. Passaram pelo filtro do universo 3.841 consolidadas e 1.050 individuais. A regra individual excluiu 2.038 referências por presença do consolidado e 753 holdings, registradas como primeiro motivo. As duas referências anuais documentalmente ambíguas em cada escopo permanecem identificadas e bloqueadas.

| Ano | Quality `con` | Distress `con` | Ambos `con` | Quality `ind` | Distress `ind` | Ambos `ind` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2019 | 0 | 33 | 0 | 86 | 89 | 85 |
| 2020 | 72 | 74 | 72 | 90 | 92 | 90 |
| 2021 | 83 | 84 | 83 | 96 | 97 | 95 |
| 2022 | 85 | 86 | 85 | 102 | 104 | 102 |
| 2023 | 114 | 113 | 113 | 104 | 107 | 104 |
| 2024 | 118 | 118 | 118 | 98 | 101 | 98 |
| 2025 | 113 | 114 | 113 | 99 | 103 | 99 |
| **Total de observações** | **585** | **622** | **584** | **675** | **693** | **673** |

Com os dois eixos calculados, foram 133 códigos CVM distintos no consolidado e 122 no individual. A contagem individual é menor que a das simulações da Sprint 03A em todos os individuais, pois esta execução exige ausência de consolidado na fonte e exclui holdings individuais do universo e dos pares. Os grupos setoriais variam em disponibilidade. Em `con`, 2019 tem 33 casos de Distress e nenhum Quality, ilustração de que o suporte estatístico e a disponibilidade de um eixo não se transferem ao outro. O CSV `sensibilidade_cobertura.csv` contém os denominadores documentais e os numeradores em cada setor FCA, ano e escopo, incluindo as combinações sem scores.

A matriz `matriz_quality_distress.png` usa uma grade de 10 pontos em cada direção, com 100 incluído na última classe. O eixo horizontal representa Quality e o vertical representa Financial Distress. Os painéis `con` e `ind` permanecem separados. As células agregam contagens de observações de emissor e exercício. `matriz_faixas.csv` também oferece os recortes anuais. Há 125 observações com caixa zero identificado, 25 delas com financiamento circulante positivo. O marcador de patrimônio líquido negativo aparece em 761 observações. As contagens diagnósticas incluem observações sem ambos os scores.

As divisões da matriz usadas para medir estabilidade são convenções geométricas de uma escala relativa. Uma região de Quality e Distress altos reúne posições relativas altas nas duas referências correspondentes. Qualquer interpretação econômica de um caso exige examinar os demonstrativos, a dívida, as datas e a composição dos pares. A matriz serve à exploração e à triagem de hipóteses de pesquisa.

## Sensibilidade e estabilidade de quadrantes

As alternativas econômicas mantêm os dois componentes de Quality com pesos de 60% e 40% e os três de Financial Distress com pesos de 40%, 40% e 20%, na ordem da tabela. O teste de métodos mantém os pesos do benchmark e compara o percentil com o z-score robusto. O z usa mediana e dispersão de $1{,}4826\times MAD$, com $IQR/1{,}349$ quando o MAD é zero e o intervalo interquartil é positivo. A transformação monotônica $100\Phi(z)$ expressa o z na escala de comparação. Referências sem dispersão utilizável deixam esse componente indisponível. [Alternativas econômicas](sprint-03a-especificacao.md#fórmulas-propostas-e-pesos) · [Protocolo de normalização](sprint-03a-normalizacao.md)

Os macrosetores candidatos são Utilidades e Transformação intensiva em ativos. Cada componente preserva a referência exata admissível e usa a candidata apenas quando a referência exata estiver indisponível. Os resultados identificam o tipo de referência por componente, inclusive combinações de níveis dentro do mesmo eixo. Ganhos de cobertura em relação ao benchmark são contabilizados à parte. Introduzir pares de outro conjunto altera a interpretação econômica da posição. Holdings, limites de 15 e 50 pares e perturbações de composição completam o diagnóstico de dependência da amostra. [Macrosetores candidatos](sprint-03a-macrosetores.md)

Para cada alternativa, mudanças em pontos usam a interseção das observações elegíveis para o eixo em análise. A comparação entre pesos econômicos e método robusto também sai na mesma interseção dos três cenários, identificada por `comum_benchmark_pesos_metodo`. Mudanças de quadrante usam a interseção dos dois eixos nas configurações em análise. Entradas e saídas ficam em colunas separadas. A sensibilidade ao próprio corte compara as mesmas observações do benchmark. As duas retiradas simuladas selecionam, após excluir o emissor, a parte inteira de 20% dos pares pela ordenação SHA-256 de código, coorte e nome do choque. Assim se varia a composição sem escolher pares pelo indicador.

Os cortes geométricos testados são 40, 50 e 60 em ambos os eixos. `Q≥·D<`, por exemplo, indica Quality no corte ou acima e Distress abaixo. Na igualdade numérica, o caso pertence à faixa `≥`. As convenções servem para medir estabilidade em uma escala contínua. No corte 50, as quatro regiões `Q<·D<`, `Q<·D≥`, `Q≥·D<` e `Q≥·D≥` contêm 107, 152, 188 e 137 observações `con`, e 152, 178, 172 e 171 `ind`.

| Cenário | Ambos `con` | Ambos `ind` | Mudanças em 50 `con` | Mudanças em 50 `ind` |
| --- | ---: | ---: | ---: | ---: |
| Benchmark, setor exato e 30 pares | 584 | 673 | Referência | Referência |
| Pesos econômicos | 584 | 673 | 79 / 584 (13,53%) | 77 / 673 (11,44%) |
| Z robusto | 584 | 673 | 57 / 584 (9,76%) | 58 / 673 (8,62%) |
| Macrosetores candidatos | 963 | 789 | 0 / 584 | 0 / 673 |
| Exclusão de holdings | 584 | 673 | 0 / 584 | 0 / 673 |
| 15 pares | 1.291 | 746 | 0 / 584 | 0 / 673 |
| 50 pares | 0 | 159 | Sem amostra comum | 0 / 159 |
| Retirada de 20%, seleção A | 457 | 673 | 28 / 457 (6,13%) | 35 / 673 (5,20%) |
| Retirada de 20%, seleção B | 457 | 673 | 31 / 457 (6,78%) | 45 / 673 (6,69%) |

Cada fração de mudança tem como denominador a amostra conjunta pareada. A comparação de pesos e método usa a mesma amostra também para cada eixo separadamente: 585/622 observações de Quality/Distress em `con` e 675/693 em `ind`. A mediana da diferença absoluta com pesos econômicos foi de 2,20 pontos para Quality e 2,44 para Distress em `con`, e 1,96 e 2,52 em `ind`. Para o método robusto, as medianas foram 2,43 e 1,97 em `con`, e 2,49 e 2,76 em `ind`. `sensibilidade_scores.csv` também traz P90 e Spearman pareado para cada recorte.

Os macrosetores acrescentaram 379 observações `con` e 116 `ind` com ambos os eixos. A estabilidade nas observações compartilhadas decorre da prioridade do setor exato, que preserva as referências já utilizáveis. As observações adicionais têm composição de referência diferente. O CSV de quadrantes apresenta as transições da amostra comparável e contabiliza essas entradas à parte. Excluir holdings centra o universo elegível em companhias operacionais com rótulos próprios. As holdings consolidadas do painel já careciam de suporte para um eixo completo a 30 pares. Os escopos individuais já as excluíam do benchmark.

Só alterar o corte do benchmark de 50 para 40 muda a região de 145 observações `con` (24,83%) e 189 `ind` (28,08%). Ao passar de 50 para 60, mudam 184 (31,51%) e 209 (31,05%), respectivamente. A posição em quadrantes depende da convenção vizinha. A tabela de transições preserva a região de origem e de destino. O choque de retirada também mostrou que a estabilidade na amostra comum pode coexistir com perda de cobertura, como as 127 observações consolidadas que perderam pelo menos um eixo em ambas as retiradas.

## Limitações e parecer de prontidão

- A DFP é anual e o painel reúne versões revistas coletadas depois do exercício correspondente. A data contábil, a de recebimento da CVM, a de coleta e a de divulgação verificável representam momentos distintos. A calibração com pares do mesmo exercício caracteriza posição relativa nessa captura. Uma aplicação histórica depende de provar que todos os valores, versões, classificações e referências já estavam disponíveis no corte. [Metodologia temporal](metodologia.md#disponibilidade-e-validação-temporal) · [Histórico e versões DFP](historico-dfp.md)
- A ausência de documentos ou de referência semelhante muda a composição da amostra e o alcance dos scores. A normalização por setor reduz diferenças de escala dentro da referência, mas também torna a posição relativa ao conjunto observado. Em uma mudança setorial comum, a ordenação relativa pode ficar estável mesmo com as razões contábeis deterioradas. Observe os valores brutos e as perdas de cobertura junto aos scores. [Cobertura e sensibilidade da Sprint 03A](sprint-03a-viabilidade.md)
- Qualidade operacional e pressão financeira têm dimensões econômicas próprias, com contas capazes de carregar informação parcialmente comum. Mudanças em giro e perímetro, itens não recorrentes, restrições a caixa e classificações de fluxos podem alterar os valores. Comparações de holdings consolidadas exigem atenção a controle e equivalência patrimonial. Comparações entre macrosetores candidatos dependem de homologação econômica. [Redundância e interpretação](sprint-03a-especificacao.md#redundância-econômica) · [Diligência dos macrosetores](sprint-03a-macrosetores.md)

**Parecer.** A prontidão desta fase é para uma análise quantitativa descritiva, reproduzível e revisável. A prontidão para validação com eventos de recuperação judicial requer concluir uma frente independente de reconstrução temporal e de curadoria de eventos.

1. Reúna versões DFP e classificações FCA historicamente disponíveis. Registre fonte, versão, hash, data pública verificável e critérios de vinculação da identidade CVM/CNPJ. Separe cancelamentos e indisponibilidade documental do estado econômico da companhia. Valide as datas com exemplos de divulgação tardia e reapresentação.
2. Especifique o evento primário antes da avaliação. Um pedido e seu deferimento podem ter datas e significados distintos. Registre a primeira evidência pública verificável de cada evento elegível, deduplique comunicados de seguimento e classifique explicitamente companhias em recuperação antes do corte. O IPE e documentos judiciais são fontes candidatas à confirmação, com rastreabilidade de cada decisão de inclusão. [Metodologia de eventos](metodologia.md#disponibilidade-e-validação-temporal)
3. Defina a população em risco, o horizonte de observação e as regras de censura ou eventos concorrentes. Preserve emissores que estavam elegíveis no corte e investigue a cobertura perdida por saída de registro, ausência de documento ou seguimento incompleto. Congele os pares, transformações e pesos em uma data de corte compatível com a divulgação pública.
4. Conclua as diligências setoriais e avalie a utilidade incremental de Quality sobre uma referência de Distress na mesma população. Use blocos cronológicos com maturação dos rótulos, teste final reservado e incerteza compatível com a repetição de emissores. Fixe os critérios de comparação e reporte cobertura e taxas observadas junto às métricas de avaliação. [Plano para a próxima validação](sprint-03b-plano.md#protocolo-temporal-a-validar)

## Reprodução e controles

Com as partições de indicadores e os intermediários DFP gerados na Sprint 02, execute na raiz do projeto.

```sh
uv sync --locked
uv run --locked python -m quantdistress.scoring.run03b
uv run --locked pytest -m 'not dados_oficiais'
```

O grupo `dev` inclui Matplotlib. Use `--painel`, `--dados` e `--saida` para apontar para outro painel, outra raiz de dados ou uma saída nova. A execução publica um diretório completo somente após terminar. O destino padrão é `outputs/sprint03b/`.

| Artefato | Conteúdo |
| --- | --- |
| `scores.parquet` e `scores_macrosetores.parquet` | Painéis separados por cenário, com CVM, CNPJ, exercício, escopo, referências, indicadores originais, componentes, eixos, pesos, marcadores e diagnósticos. |
| `componentes.parquet` e `componentes_macrosetores.parquet` | Cinco linhas por observação, com situação de origem, documento, datas, contas e linhas, tipo de referência, tamanho e dispersão. `REF_MIN`, `REF_MAX` e `REF_IQR` usam as unidades orientadas do indicador. Os hashes de pares separam a composição da referência de seus valores. |
| `matriz_quality_distress.png`, `matriz_faixas.csv` e `matriz_quadrantes.csv` | Figura agregada, grade numérica anual e contagens de quadrantes no benchmark. |
| `sensibilidade_cobertura.csv`, `sensibilidade_scores.csv`, `estabilidade_quadrantes.csv` e `transicoes_quadrantes.csv` | Abrangência e diferenças pareadas, com recortes por período, ano, escopo e setor FCA. |
| `configuracoes.json` e `manifesto.json` | Configurações, versão, IDs e hashes das partições de entrada, dos intermediários DFP e das saídas. O manifesto carrega o modo `descritivo_revisado`. |

Dados oficiais e saídas por emissor permanecem nas áreas locais ignoradas. A execução local aprovou 68 testes unitários e o teste separado de reconciliação com a DFP oficial de 2024. Os novos testes verificam sinais, monotonicidade, pesos, empates, exclusão do alvo, escopos, faltantes, referências constantes, qualidade da origem, reprodutibilidade e transições de quadrantes. [Instruções de teste](../README.md)
