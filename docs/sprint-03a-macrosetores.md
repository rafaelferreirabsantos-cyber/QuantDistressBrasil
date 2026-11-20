# Sprint 03A — Comparabilidade e cobertura dos macrosetores candidatos

ImpactUFSCar — Área de Pesquisa & Mercado. Exercício `descritivo_revisado` com os cinco componentes centrais do painel 2019–2025. A classificação FCA exata é o benchmark. Cada alternativa preserva uma referência exata utilizável e testa o macrosetor apenas no componente em que falta suporte. Ano, escopo, conceito, validade contábil e exclusão do código CVM do alvo permanecem fixos. O mínimo é de 30 emissores distintos e dois valores distintos após a exclusão.

## Agrupamentos em revisão

| Alternativa | Rótulos FCA exatos | Hipótese econômica e contábil | Verificação exigida antes de aprovar |
| --- | --- | --- | --- |
| Utilidades | Energia Elétrica e Saneamento, Serv. Água e Gás | Atividades de infraestrutura com redes ou ativos de longa duração, investimento recorrente e, em parte da população, receitas contratuais ou reguladas e financiamento de longo prazo. Direitos da concessão podem aparecer como ativo financeiro ou intangível. Isso afeta a base de ativos, o giro de caixa e a leitura dos saldos circulantes. | Identificar geração, comercialização e distribuição, operação regulada e combinação de atividades. Confrontar concessões, classificações de ativos, contratos e composição da dívida. O rótulo FCA isolado é insuficiente para homologação. [ICPC 01 — Contratos de Concessão](https://www.cpc.org.br/CPC/Documentos-Emitidos/Interpretacoes/Interpretacao?Id=10) |
| Transformação intensiva em ativos | Metalurgia e Siderurgia, Máquinas, Equipamentos, Veículos e Peças e Petroquímicos e Borracha | Operações de transformação com imobilizado, estoques, ciclo de produção e capital de giro. Financiamento de ativos e necessidade de giro afetam a liquidez e a alavancagem. | Verificar atividades dominantes e comparabilidade dos estoques e da depreciação. Revisar diferenças de exposição a insumos e commodities, câmbio, exportações, financiamento próprio e ciclo econômico. [CPC 16 — Estoques](https://www.cpc.org.br/CPC/Documentos-Emitidos/Pronunciamentos/Pronunciamento?Id=47) · [CPC 27 — Ativo Imobilizado](https://www.cpc.org.br/CPC/Documentos-Emitidos/Pronunciamentos/Pronunciamento?Id=58) |
| Combinação dos candidatos | Os dois agrupamentos disjuntos acima | Aplica o agrupamento candidato correspondente ao rótulo, com a mesma prioridade para a referência exata. | Homologar cada mapeamento separadamente e auditar a coexistência de referências exatas e macrosetoriais entre componentes. |
| Amplo exploratório | Não financeiras no mesmo escopo e ano | Mede o limite descritivo da ampliação e o efeito de uma referência heterogênea. | Uso restrito à sensibilidade. |

Rótulos de holdings mantêm sua identidade e referência exata no piloto dos agrupamentos candidatos. Construção e incorporação, comércio, mineração, petróleo e gás, transporte e outros rótulos permanecem fora desses dois mapas. A escolha reflete diferenças como reconhecimento de receita de projetos, ciclos de estoque e de financiamento, ativos de concessão e exposição setorial a commodities. O ensaio amplo pode incluir essas atividades e holdings classificadas como não financeiras, o que torna sua interpretação distinta. Instituições financeiras e demais regimes específicos continuam fora da população. Aprovação dos agrupamentos depende de revisão por companhia e modelo de operação, além do ganho de contagem.

## Efeito sobre a cobertura

Contagens de observações de emissor e ano com contas utilizáveis e referência suficiente para todos os centrais do eixo. A população por escopo contém 3.841 observações de 708 códigos CVM únicos. As contagens de emissores no período deduplicam códigos entre anos. No painel revisado, a elegibilidade histórica segue pendente para toda a população.

| Alternativa | Quality `con` | Distress `con` | Ambos `con` | Recuperadas `con` | Quality `ind` | Distress `ind` | Ambos `ind` | Recuperadas `ind` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Setor exato | 585 | 622 | 584 | 0 | 1.312 | 1.613 | 1.310 | 0 |
| Utilidades | 686 | 723 | 685 | 101 | 1.464 | 1.788 | 1.462 | 152 |
| Transformação intensiva em ativos | 863 | 901 | 862 | 278 | 1.609 | 1.948 | 1.607 | 297 |
| Combinação dos candidatos | 964 | 1.002 | 963 | 379 | 1.761 | 2.123 | 1.759 | 449 |
| Amplo exploratório | 2.578 | 2.632 | 2.576 | 1.992 | 2.984 | 3.810 | 2.982 | 1.672 |

`Recuperadas` conta observações que passam a ter ambos os núcleos no cenário. As 379 consolidadas recuperadas na combinação pertencem a 89 códigos CVM. O total de códigos com ambos os núcleos em algum ano passa de 133 a 191, pois parte já passava no benchmark em outro ano. No individual, 449 observações recuperadas pertencem a 79 códigos. O total de códigos passa de 254 a 330. No consolidado, a cobertura conjunta passa de 15,2% para 25,1% da população documental não financeira.

| Rótulo FCA | Recuperadas `con` | Recuperadas `ind` |
| --- | ---: | ---: |
| Energia Elétrica | 58 | 0 |
| Saneamento, Serv. Água e Gás | 43 | 152 |
| Metalurgia e Siderurgia | 102 | 120 |
| Máquinas, Equipamentos, Veículos e Peças | 140 | 137 |
| Petroquímicos e Borracha | 36 | 40 |

Transformação representa 278 de 379 recuperações consolidadas e 297 de 449 individuais. A mudança concentra a expansão nesses rótulos. As recuperações consolidadas por ano de 2019 a 2025 são 37, 38, 74, 78, 51, 52 e 49. As individuais são 58, 59, 59, 67, 69, 69 e 68. A referência ampla acrescentaria atividades com estrutura diferente, incluindo 148 observações consolidadas em Serviços Transporte e Logística e 118 no rótulo de holdings de Energia Elétrica. O CSV de cobertura desagrega ano, setor, escopo, eixo e alternativa.

## Sensibilidade em amostra comum

Para os valores de componentes com referência exata e macrosetorial utilizáveis, substituir a exata pelo macrosetor deslocou o percentil em mediana de 3,24 pontos no consolidado (482 comparações) e 2,18 no individual (2.614). O P90 foi de 7,98 e 5,51 pontos, respectivamente. Essa comparação mede o efeito da referência em casos já calculáveis. A simulação de recuperação mantém a exata nesses casos. As observações recuperadas carecem de uma medida correspondente no benchmark exato.

A referência ampla produziu mudanças acima de 10 pontos em cerca de 38% das comparações consolidadas e 36% das individuais com referência exata disponível. Diferenças de composição explicam parte da alteração. Um aumento de cobertura só é útil após validar as características operacionais e contábeis dos pares e definir quando os dois níveis de referência podem coexistir no mesmo eixo. [Protocolos completos, resultados e reprodução](sprint-03a-revisao-final.md)
