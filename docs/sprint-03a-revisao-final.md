# Sprint 03A — Revisão final do PR #2

ImpactUFSCar — Área de Pesquisa & Mercado. Os experimentos usam as sete partições do painel de 2019 a 2025 e têm modo `descritivo_revisado`. Preservam os cinco centrais e os pesos iguais do benchmark. As alternativas econômicas permanecem propostas fixas de sensibilidade. A revisão se limita à especificação científica e a diagnósticos agregados. [Especificação](sprint-03a-especificacao.md) · [Viabilidade original](sprint-03a-viabilidade.md)

| Problema identificado | Correção |
| --- | --- |
| Os resultados da referência inclusiva podiam ser confundidos com exclusão do alvo ou calibração histórica. | Protocolos identificados nas saídas. O novo comparador exclui por código CVM antes de contar e avaliar dispersão. Os testes verificam referência exata, vintages, empates, constantes, faltantes e os limites 15, 30 e 50. |
| O choque em um máximo cobria só um mecanismo de instabilidade. | Testes em amostra comum para entrada, saída, valores intermediários, mudança do indicador, composição setorial e janela temporal. |
| A fórmula escalar de suporte misturava disponibilidades e aplicava uma penalidade arbitrária ao macrosetor. | O diagnóstico registra disponibilidade dos componentes, suporte estatístico, qualidade contábil e elegibilidade temporal em quatro dimensões distintas. |
| A referência ampla elevava cobertura sem demonstrar comparabilidade. | O setor exato segue como referência primária. Dois agrupamentos operacionais candidatos foram comparados separadamente e em conjunto. A referência ampla fica restrita ao experimento. |

## Protocolos e limiares

Escolha a última referência por código CVM, ano, escopo e indicador antes de filtrar a validade. Uma última entrega ambígua ou inválida fica sem uso, com preservação das contagens de exclusão na análise de viabilidade. Cada referência contém uma linha válida por código CVM. A referência exata separa `SETOR_FCA`, ano, escopo e indicador. A referência excluída retira todo registro do código CVM do alvo, inclusive se estiver no ano anterior. O comparador inclusivo usa a mesma base exata e conserva o alvo. O experimento original da rodada anterior mantém a sua base de nove indicadores e protocolo inclusivo como registro da comparação de transformações. [Normalização original](sprint-03a-normalizacao.md)

| Escopo | Valores dos cinco centrais com referência inclusiva | Com exclusão do alvo | Diferença | Maior diferença entre posições comparáveis |
| --- | ---: | ---: | ---: | ---: |
| Consolidado | 3.223 | 3.073 | 150 | 1,61 ponto |
| Individual | 7.975 | 7.765 | 210 | 1,56 ponto |

As contagens são valores-indicador, não companhias únicas. Incluir o alvo pode fazer um grupo com 30 observações passar quando só há 29 pares externos. Para um alvo entre os $n$ valores, o percentil inclusivo é $((n-1)P_{\mathrm{excl}}+50)/n$ quando ambas as referências são utilizáveis. O deslocamento em pontos fica limitado a $50/n$ e a mudança de admissibilidade no limiar é separada desse deslocamento. Ausentes ou não finitos ficam indisponíveis. Empates recebem ponto médio. Uma distribuição constante depois da exclusão também fica indisponível.

## Choques de robustez

O comparador usa percentil de ponto médio no setor exato após excluir o alvo e com mínimo de 30 pares. Os choques mantêm o alvo fixo, exceto quando a intervenção muda seu próprio indicador. Os cenários de composição coletam até 20% do grupo inicial, arredondado para baixo. A seleção de códigos usa uma ordenação determinística por SHA-256 com chave da coorte, independente do valor financeiro. Após o choque, os controles de exclusão, tamanho e dispersão voltam a ser aplicados.

| Cenário | Intervenção |
| --- | --- |
| Entrada | Junta códigos do setor, escopo e indicador no ano anterior ausentes da coorte documental contemporânea. Exige valor válido e rastreável. Simula entrada no grupo, inclusive por mudança de composição. |
| Saída | Retira até 20% da distribuição de referência por seleção de códigos. |
| Composição setorial | Troca parte dos pares por códigos do outro setor do mesmo macrosetor candidato, preservando o tamanho antes da exclusão do alvo. O teste vale nos setores mapeados e onde a troca é viável. |
| Valores intermediários | Adiciona meio intervalo interquartil aos pares entre P40 e P60 da referência original. Empates nos limites seguem o mesmo critério. |
| Perturbação do indicador | Desloca o valor do alvo em mais ou menos 0,1 intervalo interquartil dos pares, com referência fixa. |
| Referência temporal | Usa valores do mesmo setor, indicador e escopo no ano anterior, excluindo o código do alvo. |
| Macrosetor ou grupo amplo | Compara as posições nas duas referências. Na política de cobertura, a exata continua prioritária. |
| Cauda | Amplia um máximo em 100 vezes a amplitude da referência, como controle da sensibilidade à magnitude isolada. |

| Cenário | Comparáveis `con` | P90 da mudança `con` | Comparáveis `ind` | P90 da mudança `ind` | Perdas de suporte `con` / `ind` |
| --- | ---: | ---: | ---: | ---: | ---: |
| Entrada | 2.489 | 2,38 | 6.185 | 1,95 | 0 / 0 |
| Saída | 2.305 | 5,32 | 7.140 | 4,13 | 768 / 625 |
| Composição setorial | 482 | 9,38 | 2.614 | 5,71 | 0 / 0 |
| Valores intermediários | 3.073 | 17,50 | 7.765 | 18,06 | 0 / 0 |
| Indicador +0,1 IQR | 3.073 | 9,30 | 7.765 | 8,86 | 0 / 0 |
| Indicador −0,1 IQR | 3.073 | 9,30 | 7.765 | 8,86 | 0 / 0 |
| Referência do ano anterior | 2.598 | 11,72 | 6.792 | 9,59 | 344 / 216 |
| Macrosetor candidato | 482 | 7,98 | 2.614 | 5,51 | 0 / 0 |
| Amplo exploratório | 3.073 | 21,17 | 7.765 | 19,75 | 0 / 0 |
| Cauda | 2.994 | 0,00 | 7.632 | 0,00 | 0 / 0 |

As diferenças são absolutas em pontos percentílicos. Perdas são valores com referência utilizável no comparador e indisponível após o choque. Cada cenário conta apenas os casos de intervenção aplicável. A entrada acrescentou suporte para 150 valores no consolidado e 239 no individual. A troca de composição acrescentou 30 e 42, respectivamente. Os tamanhos do conjunto comum variam. O percentil foi sensível à massa de valores intermediários e à composição. No choque intermediário, cerca de 23% dos pares variaram mais de 10 pontos em ambos os escopos. O choque no máximo deixou as posições comparáveis estáveis e a saída de pares reduziu a cobertura. O CSV dá visibilidade às perdas, ganhos e distribuição das mudanças por ano, setor e indicador.

## Suporte estatístico e contábil

Cada escopo tem 19.205 combinações de observação e componente na população não financeira de referência única. A contabilidade capturou 13.103 valores centrais consolidados e 18.225 individuais com insumos automaticamente vinculados ao documento. Isso registra rastreabilidade disponível no painel. Uma auditoria independente dos valores e dos casos extremos pede revisão humana.

| Dimensões do diagnóstico | Consolidado | Individual |
| --- | ---: | ---: |
| Valor disponível e referência exata utilizável | 3.073 | 7.765 |
| Valor disponível e referência exata insuficiente | 10.030 | 10.460 |
| Valor indisponível e referência exata utilizável | 1.247 | 274 |
| Valor indisponível e referência exata insuficiente | 4.855 | 706 |

As dimensões capturam falhas diferentes. No consolidado, a primeira falha foi `sem_fatos` em 5.985 combinações e `denominador_invalido` em 92. No individual, foram 70 e 849, respectivamente. O número de pares e a massa do maior empate são descritores empíricos. O limiar e o requisito de variabilidade são decisões metodológicas. A dimensão temporal registra ausência de data em todas essas combinações. Uma informação de data ainda sem verificação também ficaria em diligência, separada da disponibilidade do valor. [Especificação do diagnóstico e limites](sprint-03a-especificacao.md)

## Parecer para a Sprint 03B

A base e os testes sustentam a implementação descritiva, condicionada à aprovação da Área de Pesquisa & Mercado. A recomendação é preservar a referência exata, excluir o alvo, exigir os cinco centrais nas suas respectivas composições fixas e carregar os diagnósticos separados na saída. A decisão sobre macrosetores precisa validar os pares econômicos e contábeis e a política de convivência entre referências. A combinação candidata recupera 379 observações consolidadas e 449 individuais para ambos os núcleos. [Cobertura e composição por agrupamento](sprint-03a-macrosetores.md)

Ainda dependem de decisão o piso de 30 pares, a estabilidade mínima que a equipe considera aceitável, as diligências de holdings e o tratamento dos casos extremos. A implementação histórica depende de dados com divulgação e versão verificáveis e de coortes congeladas na data de corte. O piloto de ano anterior usa informação revisada coletada posteriormente. Backtests e avaliações preditivas permanecem bloqueados no painel atual. [Plano da Sprint 03B](sprint-03b-plano.md) · [Limitações temporais da DFP](historico-dfp.md)

## Reprodução

```sh
uv run --locked python -m quantdistress.evaluation.revision03
uv run --locked pytest -m 'not dados_oficiais'
```

O primeiro comando lê o painel da Sprint 02. Em `outputs/sprint03a-revisao/`, gera `robustez_percentil.csv`, `cobertura_macrosetores.csv`, `suporte_componentes.csv` e um manifesto com o hash do manifesto de entrada. As saídas têm somente recortes agregados e identificam o caráter descritivo revisado. O teste com arquivo oficial segue como etapa separada. [Execução do teste oficial](../README.md)
