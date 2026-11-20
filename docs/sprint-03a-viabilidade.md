# Sprint 03A — Cobertura conjunta e viabilidade dos scores

ImpactUFSCar — Pesquisa & Mercado. O estudo usa o painel descritivo revisado da Sprint 02, com capturas anuais de 2019 a 2025. Os resultados descrevem a viabilidade contábil das propostas. O cálculo histórico dos scores depende de evidência de divulgação e da aprovação metodológica. [Inventário e hashes das fontes](historico-dfp.md) · [Especificação proposta](sprint-03a-especificacao.md)

A revisão final reproduz o benchmark exato e mede separadamente a inclusão do alvo, a robustez a mudanças de referência e o efeito de macrosetores candidatos. As contagens desta página conservam o piloto original. [Resultados da revisão final](sprint-03a-revisao-final.md)

## Base, unidade e filtros

O painel tem 5.019 referências e 10.038 observações quando se contam os dois escopos. Abrange 909 códigos CVM únicos no período e 907 CNPJs distintos. Dois CNPJs foram vinculados a dois códigos CVM cada. As tabelas de emissores usam o código CVM como identidade cadastral e deixam a equivalência jurídica ou econômica para diligência. As frequências por observação contam exercícios. As quantidades de emissores no período deduplicam o código entre anos e setores do recorte. A soma das contagens setoriais de emissores pode exceder a quantidade de emissores do período.

Os diagnósticos contábeis mantêm todas as referências do painel. Para os experimentos de elegibilidade, selecionei a última referência por código CVM, ano de arquivo e escopo antes de olhar os valores. Esse critério removeu 11 referências por escopo. Restaram 5.008, das quais 5.006 têm entrega inequívoca e 3.841 são não financeiras. Ausências de demonstrações contam no denominador dessa população. O teste de ausência do consolidado verifica fatos correntes no Parquet original da DFP, antes da seleção por versão e conflito. Um consolidado incompleto continua sendo tratado como consolidado presente.

## Cobertura dos indicadores

Contagens consolidadas do grupo não financeiro, considerando as 3.846 referências por escopo antes da seleção anual. Razões em unidades por unidade. Os quantis e extremos descrevem os valores aprovados nas regras contábeis da Sprint 02.

| Indicador | Observações válidas | Emissores CVM válidos | P01 | Mediana | P99 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Margem operacional | 2.582 | 484 | −5,826 | 0,131 | 1,795 |
| Rentabilidade operacional sobre ativos | 2.624 | 494 | −0,400 | 0,073 | 0,388 |
| Caixa operacional sobre receita | 2.583 | 484 | −2,965 | 0,109 | 1,060 |
| Giro do ativo | 2.621 | 494 | 0,000 | 0,503 | 2,455 |
| Crescimento da receita | 2.537 | 478 | −0,716 | 0,118 | 3,291 |
| Liquidez corrente | 2.635 | 496 | 0,028 | 1,531 | 8,325 |
| Patrimônio líquido sobre ativo | 2.635 | 496 | −6,245 | 0,332 | 0,903 |
| Financiamentos reportados sobre ativo | 2.635 | 496 | 0,000 | 0,312 | 1,956 |
| Financiamentos circulantes sobre caixa | 2.614 | 492 | 0,000 | 0,853 | 750,652 |

O máximo foi 3.334 em liquidez corrente e 38.178,341 em financiamentos circulantes sobre caixa. O patrimônio sobre ativo chegou a −233,720. A classificação `valido` atesta os controles da fórmula atual. Casos extremos ainda requerem revisão de escala, unidade, materialidade econômica do denominador e contexto contábil. O diagnóstico registra P01, P05, quartis, P95, P99, mínimos, máximos e contagem de caudas por ano, setor e escopo. O agregado conta múltiplos exercícios de um mesmo emissor e tem caráter descritivo. [Regras dos indicadores](conceitos-indicadores.md)

## Cobertura conjunta e impacto das exclusões

O núcleo **Quality** exige rentabilidade operacional sobre ativos e caixa operacional sobre receita. O núcleo **Distress** exige liquidez corrente, patrimônio líquido sobre ativos e financiamentos reportados sobre ativos. As contagens em conjunto medem disponibilidade dos dois eixos. Os critérios genéricos de quantidade são cenários de cobertura.

| Ano | Referências não financeiras por escopo | Quality núcleo `con` | Distress núcleo `con` | Ambos `con` | Nove indicadores `con` | Ambos com 30 pares exatos `con` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2019 | 443 | 277 | 290 | 277 | 273 | 0 |
| 2020 | 501 | 337 | 345 | 337 | 323 | 72 |
| 2021 | 562 | 378 | 390 | 378 | 367 | 83 |
| 2022 | 578 | 391 | 400 | 391 | 380 | 85 |
| 2023 | 587 | 398 | 400 | 397 | 389 | 113 |
| 2024 | 593 | 408 | 412 | 407 | 399 | 118 |
| 2025 | 577 | 389 | 395 | 389 | 381 | 113 |
| Total | **3.841** | **2.578** | **2.632** | **2.576** | **2.512** | **584** |

| Critério de disponibilidade após a seleção anual | Consolidado | Individual |
| --- | ---: | ---: |
| Quality com pelo menos 3 de 5 quaisquer | 2.582 | 3.006 |
| Quality com pelo menos 4 de 5 quaisquer | 2.578 | 2.984 |
| Quality com 5 de 5 | 2.531 | 2.930 |
| Quality com os 2 centrais | 2.578 | 2.984 |
| Distress com pelo menos 2 de 4 quaisquer | 2.632 | 3.814 |
| Distress com pelo menos 3 de 4 quaisquer | 2.632 | 3.811 |
| Distress com 4 de 4 | 2.611 | 3.727 |
| Distress com os 3 centrais | 2.632 | 3.810 |
| Ambos os núcleos | 2.576 observações / 483 emissores | 2.982 observações / 552 emissores |
| Nove indicadores | 2.512 observações / 473 emissores | 2.892 observações / 539 emissores |

Uma contagem global igual pode ocultar conjuntos distintos de indicadores. A regra proposta exige todos os centrais de cada eixo. O Quality ganha 47 observações consolidadas em relação à exigência de cinco componentes. A interseção dos dois núcleos ganha 64 em relação à exigência dos nove indicadores.

Em 2024, a disponibilidade dos dois núcleos no consolidado variou entre Energia Elétrica (33 de 84 referências), Serviços Transporte e Logística (28 de 80), Construção Civil (44 de 48) e Comércio (41 de 45). As diferenças combinam a composição da população e a presença documental. `experimentos_cobertura.csv` contém os recortes completos de ano, setor FCA e escopo, inclusive as causas de redução de cobertura observáveis nas demais tabelas.

### Holdings e escopo individual

O prefixo `Emp. Adm. Part. - ` identifica 1.076 referências após a seleção anual, 21,5% das 5.008 em cada escopo. Entre as 3.841 referências não financeiras, há 753 holdings (19,6%). No consolidado, 572 referências de holdings dispõem dos dois núcleos. Excluí-las reduz a população não financeira para 3.088 observações e a cobertura simultânea para 2.004, de 376 emissores. O rótulo do FCA é um indicador cadastral da estrutura. Controle efetivo e perímetro de consolidação ainda requerem revisão.

No estrato individual, há 1.197 referências não financeiras sem consolidado corrente na fonte. Ao excluir holdings, restam 1.050 referências, das quais 988 (196 códigos CVM) têm os dois núcleos disponíveis. Esse estrato é candidato a experimento separado, com referência e interpretação individuais. Os resultados de `con` e `ind` incluem populações diferentes.

### Tamanho mínimo da referência e tempo

O teste conjuntural abaixo usa o setor FCA exato, ano e escopo. Para cada componente, remove o emissor avaliado, exige dispersão entre os demais e verifica a quantidade mínima de pares. A contagem exige referência suficiente para todos os componentes dos dois núcleos. Ela mede viabilidade descritiva com amostra contemporânea, sem calcular índice composto.

| Pares distintos mínimos por componente | Ambos `con` | Ambos `ind` |
| --- | ---: | ---: |
| 15 | 1.291 observações / 258 emissores | 1.961 observações / 367 emissores |
| 30 | 584 observações / 133 emissores | 1.310 observações / 254 emissores |
| 50 | 0 | 915 observações / 165 emissores |

O limiar de 30 reduz o conjunto consolidado com ambos os núcleos de 2.576 para 584 observações. O resultado recomenda experimentar macrosetores comparáveis aprovados pela equipe e medir a perda ou mudança de referência. A população ampla não financeira serve à análise de sensibilidade. Todas as datas de divulgação estão ausentes no painel. A cobertura para a aplicação histórica proposta é **zero** até que a disponibilidade de cada insumo e referência fique demonstrada. [Comparação de normalização](sprint-03a-normalizacao.md) · [Limitações temporais](historico-dfp.md)

## Denominadores, conflitos e sensibilidade contábil

O painel registra a primeira regra impeditiva. A auditoria usa a linhagem dos insumos quando a razão chega à divisão e reconstrói a escala original com aritmética decimal. Os casos interrompidos antes da divisão ficam na categoria `divisao_nao_avaliada`. As proporções abaixo usam apenas divisões avaliadas, inclusive as bloqueadas por denominador não positivo.

| Indicador | Zeros `con` | Negativos `con` | Divisões avaliadas `con` | Zeros `ind` | Negativos `ind` | Divisões avaliadas `ind` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Margem operacional | 48 | 4 | 2.634 | 796 | 17 | 3.800 |
| Rentabilidade sobre ativos | 7 | 0 | 2.631 | 8 | 0 | 3.796 |
| Caixa operacional sobre receita | 48 | 4 | 2.635 | 796 | 17 | 3.801 |
| Giro do ativo | 7 | 0 | 2.628 | 8 | 0 | 3.780 |
| Crescimento da receita | 82 | 2 | 2.621 | 801 | 11 | 3.764 |
| Liquidez corrente | 11 | 0 | 2.646 | 4 | 0 | 3.832 |
| Patrimônio líquido sobre ativo | 11 | 0 | 2.646 | 12 | 0 | 3.831 |
| Financiamentos reportados sobre ativo | 11 | 0 | 2.646 | 12 | 0 | 3.829 |
| Financiamentos circulantes sobre caixa | 30 | 0 | 2.644 | 95 | 0 | 3.828 |

Caixa zero aparece em 1,1% das divisões consolidadas avaliadas na razão de curto prazo e em 2,5% das individuais. Entre os zeros, 8 referências consolidadas e 17 individuais têm financiamento circulante positivo, enquanto 22 e 78 têm financiamento circulante zero. O marcador de estado é separado da razão, que permanece indisponível. Admitir a presença desse marcador como evidência complementar eleva a cobertura do Distress com alguma medida de pressão de 2.611 para 2.619 referências no consolidado e de 3.727 para 3.744 no individual. Há 308 ocorrências consolidadas e 453 individuais de patrimônio líquido negativo entre as razões válidas. O sinal negativo permanece economicamente informativo.

| Mudança de definição, pares consolidados | Observações | Spearman | Mediana da mudança absoluta | P90 da mudança absoluta |
| --- | ---: | ---: | ---: | ---: |
| Rentabilidade com ativo final no lugar do ativo médio | 2.620 | 0,991 | 0,41 p.p. | 2,40 p.p. |
| Giro com ativo final no lugar do ativo médio | 2.617 | 0,984 | 0,025 vez | 0,135 vez |
| Somente financiamento circulante sobre ativo, frente à soma circulante e não circulante | 2.632 | 0,549 | 21,10 p.p. | 52,51 p.p. |

As comparações usam os mesmos casos válidos e excluem os denominadores sem validade na alternativa. O ativo médio continua sendo a base de comparação com o fluxo anual. A mudança de composição de financiamentos tem efeito material e caracteriza uma medida diferente. As fontes cobrem os agregados identificados da DFP. A composição de toda a dívida onerosa depende de diligência adicional. A DFC direta contribui com 64 razões válidas de caixa operacional sobre receita em `con`, diante de 2.519 pela indireta. Em `ind`, são 72 e 2.916. Esses métodos cobrem emissores diferentes e a comparação de medianas por método é descritiva.

## Correlação e redundância

Consolidado não financeiro, todas as referências. Pearson com valores limitados a P01–P99 para cada variável apresenta um teste de sensibilidade no par. Spearman mede associação monotônica com postos médios em empates. O cálculo exige ao menos dez observações e dez códigos CVM pareados, além de dispersão. Os recortes agrupados de vários anos contêm observações repetidas por emissor e servem para diagnóstico, sem inferência de significância. Para os recortes ano × setor FCA × par de indicadores, 3.396 puderam ser calculados no consolidado e 7.764 tinham amostra insuficiente. O relatório de correlações registra o motivo quando uma estimativa fica ausente.

| Par | Observações / emissores | Pearson | Pearson P01–P99 | Spearman |
| --- | ---: | ---: | ---: | ---: |
| Margem e rentabilidade | 2.578 / 483 | 0,554 | 0,569 | 0,735 |
| Rentabilidade e caixa operacional sobre receita | 2.578 / 483 | −0,056 | 0,230 | 0,285 |
| Margem e caixa operacional sobre receita | 2.582 / 484 | −0,048 | 0,380 | 0,467 |
| Patrimônio sobre ativo e financiamentos sobre ativo | 2.635 / 496 | −0,953 | −0,596 | −0,611 |
| Liquidez corrente e patrimônio sobre ativo | 2.635 / 496 | 0,005 | 0,342 | 0,574 |
| Liquidez corrente e financiamento circulante sobre caixa | 2.614 / 492 | −0,003 | −0,181 | −0,426 |

A identidade `rentabilidade = margem × giro` foi confirmada nos 2.578 casos consolidados e 2.984 individuais com os três indicadores disponíveis. O erro absoluto máximo foi inferior a `2 × 10⁻¹⁵`. A especificação mantém rentabilidade no núcleo e usa margem e giro para decomposição. A posição menor da associação entre rentabilidade e caixa operacional apoia a análise dos dois como perspectivas complementares. No Distress, patrimônio e financiamento compartilham o ativo como divisor e parte da estrutura econômica. A associação persiste após o controle de caudas, com magnitude menor. Isso motiva testar menor peso para a medida de financiamentos reportados, mantendo a regra de cobertura e a decisão sujeitas à revisão.

## Decisões para aprovação

1. Aprovar a composição fixa de dois centrais no Quality e três no Distress. Usar pesos iguais como referência e os pesos econômicos propostos como sensibilidade declarada. Os demais indicadores explicam as dimensões ou registram estados de pressão.
2. Revisar a elegibilidade das holdings e o universo de comparação individual. Confirmar critérios contábeis e regras dos macrosetores, inclusive o patamar piloto de 30 pares e a política de referência insuficiente.
3. Aprovar percentil de ponto médio como benchmark provisório. Manter z-score clássico e robusto como testes de sensibilidade. Em produção histórica, congelar referências e transformações com dados cuja disponibilidade esteja comprovada.
4. Exigir validação da linhagem temporal, diligência das caudas e revisão da composição de financiamentos antes de autorizar implantação ou avaliação prospectiva. [Plano Sprint 03B](sprint-03b-plano.md)

## Reprodução e leitura das tabelas

Gere primeiro as partições e os Parquet de ingestão da Sprint 02. Depois execute na raiz do repositório.

```bash
uv run --locked python -m quantdistress.evaluation.diagnostics03
uv run --locked python -m quantdistress.evaluation.feasibility03
uv run --locked python -m quantdistress.evaluation.normalization03
uv run --locked pytest -m 'not dados_oficiais'
```

`outputs/sprint03a-diagnosticos/` contém cobertura individual, cobertura conjunta, distribuições, correlações, situações, denominadores e a identidade margem × giro. `outputs/sprint03a-viabilidade/` contém os cenários de elegibilidade, amostras exatas, exclusões e estados, variantes contábeis e métodos de DFC. A normalização grava comparações agregadas em `outputs/sprint03a/`. Os módulos geram contagens, estatísticas e sensibilidades, sem exportar uma lista ordenada de emissores.
