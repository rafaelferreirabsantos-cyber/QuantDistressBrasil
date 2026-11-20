# Sprint 03A — Viabilidade da normalização

## Métodos comparados

Em cada referência, `R` é o conjunto de valores finitos do indicador e `n` é o número de emissores com valor válido. O experimento calculou transformações univariadas para medir diferenças agregadas em pontos.

| Método | Transformação do valor `x` | Interpretação e limitação |
| --- | --- | --- |
| Percentil empírico de ponto médio | `100 × (n(R < x) + 0,5 × n(R = x)) / n` | A massa dos empates é distribuída pelo ponto médio. Um valor extremo afeta outros pontos pelo número de posições que desloca. A distância econômica entre valores fica fora da medida. Alvos fora da faixa de calibração chegam a 0 ou 100. |
| Z clássico | `z = (x − média(R)) / desvio(R)`, com divisor `n` | Preserva distância em unidades de desvio. Média e escala respondem intensamente a caudas longas e denominadores pequenos. |
| Z robusto | `zᵣ = (x − mediana(R)) / (1,4826 × MAD(R))` | A mediana absoluta dos desvios reduz a influência da cauda sobre a escala. Se `MAD = 0`, usa `IQR / 1,349` quando positivo. Quando as duas escalas são zero, a alternativa robusta fica indisponível. |
| Referência setorial | Aplica cada transformação dentro do setor, preservando o escopo | A comparação entre pares enfrenta grupos pequenos, concentração em um emissor ou poucos valores distintos. Alterar o grupo de referência altera o significado do ponto. |

Para comparar os dois z com o percentil, o experimento converteu `z` ou `zᵣ` em `100 × Φ(z)`, com `Φ` a distribuição normal padrão. Essa transformação é monotônica e expressa distâncias em uma escala comum. Eventuais saturações nas caudas decorrem da transformação. A escala tem uso descritivo e sua interpretação é relativa à referência. [Percentil de ponto médio](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.percentileofscore.html) · [Medidas de escala do NIST](https://itl.nist.gov/div898/handbook/eda/section3/eda356.htm)

## Experimento no painel de 2019 a 2025

O protocolo escolhe a última data de referência disponível por ano, escopo, código CVM e indicador antes de filtrar os valores válidos. Uma referência final inválida permanece fora da calibração, assim como um empate documental nessa data. O recorte usa o grupo não financeiro, com escopos `con` e `ind` separados. Foram 23.454 valores-indicador válidos no consolidado e 31.664 no individual. O mesmo emissor pode aparecer em vários anos ou indicadores. Dentro da referência de um indicador, cada código CVM entra uma vez.

As comparações mantêm fixos os alvos. No teste de cauda, a calibração troca apenas um máximo `m` por `m + 100 × amplitude(R)`, mantendo o tamanho da referência. A comparação temporal alterna entre a distribuição do ano de referência e a do ano calendário imediatamente anterior, sem consultar anos posteriores. O diagnóstico temporal usa versões revisadas coletadas na Sprint 02. As datas de divulgação permanecem em diligência e essas comparações medem dependência da referência. [Histórico DFP](historico-dfp.md)

### Sensibilidade em pontos

Percentuais de valores comparáveis com mudança absoluta superior a 10 pontos. A comparação setorial usa apenas observações com referência exata válida no setor do FCA e pelo menos 30 emissores. Nas comparações temporais, 2019 fica fora por falta do ano anterior.

| Comparação | Método | Consolidado | Individual |
| --- | --- | ---: | ---: |
| Cauda perturbada versus calibração observada | Percentil | 0,00% | 0,00% |
| Cauda perturbada versus calibração observada | Z robusto | 0,00% | 0,00% |
| Cauda perturbada versus calibração observada | Z clássico | 25,76% | 14,06% |
| Ano anterior versus contemporâneo, referência ampla | Percentil | 6,47% | 3,74% |
| Setor exato versus referência ampla contemporânea | Percentil | 37,49% | 36,52% |
| Z robusto versus percentil, referência ampla contemporânea | Métodos em 0–100 | 5,39% | 12,39% |
| Z clássico versus percentil, referência ampla contemporânea | Métodos em 0–100 | 63,88% | 72,73% |

O teste de cauda avalia a influência de uma única observação extrema. Sua baixa incidência nos métodos robustos para esta perturbação específica convive com diferenças de forma nas distribuições e de composição do universo. As diferenças entre percentil setorial e amplo justificam explicitar a referência efetiva em qualquer análise futura.

### Disponibilidade da referência setorial

Proporção dos valores válidos que encontram referência no próprio setor e escopo no ano, antes de fallback. A disponibilidade varia por indicador porque o número de valores utilizáveis muda.

| Mínimo de pares no setor exato | Consolidado | Individual |
| ---: | ---: | ---: |
| 15 | 54,21% (12.714) | 68,98% (21.842) |
| 30 | 24,36% (5.713) | 43,76% (13.857) |
| 50 | 0,00% (0) | 28,39% (8.989) |

No limiar de 30, 17.741 valores consolidados e 17.807 individuais recorreram à referência ampla experimental de não financeiras no mesmo escopo e ano. A alternativa ampla mede a sensibilidade do desenho. Seu uso em produção exigiria demonstrar comparabilidade econômica e aprovar o mapeamento dos setores.

## Política proposta para revisão

1. Usar o percentil empírico de ponto médio como referência de desenho e o z robusto como sensibilidade. Aplicar o sinal econômico do indicador antes de normalizar, para que a direção seja consistente dentro de cada eixo. Conservar o valor bruto, a seleção da referência e os diagnósticos de cauda. Um extremo economicamente fundamentado permanece registrado. Eventual truncamento requer uma regra e um teste de sensibilidade definidos antes da validação.
2. Exigir 30 emissores distintos com valores válidos e ao menos dois valores diferentes no setor, escopo e indicador. O piso é provisório. Mesmo sem empates, um passo de contagem com 30 pares equivale a aproximadamente 3,33 pontos. Investigar sensibilidade a 15 e 50 e estabilidade por período antes de aprovar o piso.
3. Se o setor não atender ao piso, admitir apenas um macrosetor economicamente justificável, mapeado e versionado antes da avaliação, com o mesmo escopo e os mesmos controles de contagem e dispersão. Sem referência admissível, a transformação fica indisponível. Registrar nível de referência, número de emissores, data de congelamento, mapeamento utilizado e método. O resultado relativo a um macrosetor tem população de comparação própria.
4. Um valor ausente, inválido ou não finito fica sem transformação. Empates recebem o mesmo percentil. Uma distribuição constante deixa o percentil sem informação discriminante e os z indefinidos. As regras de completude, pesos e confiabilidade pertencem à especificação dos eixos em revisão.
5. A calibração histórica deve ser congelada com versões, valores e classificações cuja disponibilidade tenha evidência anterior ao corte. Arquivar a lista de pares e as estatísticas usadas na normalização. Quando a evidência de divulgação tiver precisão de dia, adotar previamente uma convenção conservadora de disponibilidade. A mesma regra deve ser aplicada a emissores retidos ou posteriormente cancelados. Os cenários contemporâneo e de ano anterior publicados nesta sprint são diagnósticos retroativos do painel revisado.

## Reprodução

Com o painel da Sprint 02 em `data/processed/sprint02`, execute na raiz do repositório.

```sh
uv run --locked python -m quantdistress.evaluation.normalization03
uv run --locked python -m quantdistress.evaluation.normalization03 --min-pares 15 --saida outputs/sprint03a/normalizacao_min15.csv
uv run --locked python -m quantdistress.evaluation.normalization03 --min-pares 50 --saida outputs/sprint03a/normalizacao_min50.csv
uv run --locked pytest -q tests/test_normalization03.py
```

Cada CSV local traz 378 linhas agregadas por método, ano, indicador e escopo no painel de referência. Os campos descrevem contagens, mediana e percentil 90 das mudanças em pontos e número de mudanças acima de 10 pontos. Os testes exercitam empates, exclusão de valores não finitos, degeneração da escala, perturbação da cauda, separação de escopos, fallback setorial e uso estrito do ano anterior.
