# Sprint 03A — Especificação proposta dos scores

ImpactUFSCar — Pesquisa & Mercado

O **Quality / Operational Score** mede desempenho operacional relativo e aumenta com a qualidade operacional observada. O **Financial Distress Score** mede pressão financeira relativa e aumenta com o estresse observado no balanço. Cada eixo tem componentes, condições de cálculo e diagnóstico de confiabilidade próprios. O nome «distress» descreve a construção do índice contábil. Probabilidade de inadimplência, recuperação e retorno de investimento exigem definições de evento, horizontes e modelos próprios. Os pesos, as faixas de qualidade de referência e a população abaixo são propostas para aprovação da Pesquisa & Mercado.

## Unidade, contas e indicadores

A unidade de análise é a versão inequívoca da entrega de um emissor, data de referência e escopo. A contagem de emissores usa código CVM único dentro da população indicada. O CNPJ participa do vínculo e da diligência de identidades. Uma observação requer compatibilidade das linhas por data, documento, escopo, moeda e escala. Comparativos vêm da mesma entrega e pertencem à sua edição, inclusive quando reapresentados. Para análises anuais, escolha uma referência por emissor, ano e escopo antes de filtrar a validade dos indicadores. No piloto, use a última referência do ano. Empates na mesma referência sem vínculo inequívoco deixam a observação bloqueada e entram nas contagens de exclusão. [Conceitos e linhagem da Sprint 02](conceitos-indicadores.md)

Considere $E$ o resultado antes do resultado financeiro e dos tributos da DRE `3.05`, $V_t$ a receita de bens e serviços da DRE `3.01`, $O$ o fluxo de caixa das atividades operacionais da DFC `6.01`, $A_0$ e $A_1$ os saldos de ativo total no início e no fim do exercício, e $\bar A=(A_0+A_1)/2$. No fechamento, $AC$ é o ativo circulante, $PC$ o passivo circulante, $PL$ o patrimônio líquido, $F_C$ e $F_L$ os agregados reportados de empréstimos e financiamentos circulantes e não circulantes e $C$ o saldo de caixa e equivalentes. Todos são valores monetários reconciliados em reais. Razões são adimensionais, exibíveis em múltiplos ou em percentuais conforme a variável. [Dicionário de contas CVM](conceitos-indicadores.md)

| Eixo | Indicador e fórmula | Direção para o eixo | Papel proposto e interpretação |
| --- | --- | --- | --- |
| Quality | Margem operacional $E/V_t$ | Crescente | Complementar. Resultado operacional por unidade de receita. Ajuda a decompor a rentabilidade. |
| Quality | Rentabilidade operacional sobre ativos $E/\bar A$ | Crescente | Central. Combina resultado e base de ativos. O ativo contábil inclui itens que podem ficar fora de uma definição de capital operacional. |
| Quality | Caixa operacional sobre receita $O/V_t$ | Crescente | Central. Capacidade observada de converter receita em caixa. A classificação de juros, tributos e a liberação temporária de capital de giro afetam a comparação. |
| Quality | Giro do ativo $V_t/\bar A$ | Crescente em pares comparáveis | Complementar. Rotação da base de ativos e sensibilidade à intensidade de capital. |
| Quality | Crescimento da receita $V_t/V_{t-1}-1$ | Crescente para o diagnóstico | Complementar. Receita nominal de exercícios contíguos. Inflação, aquisições e expansão com margens negativas podem elevar o crescimento sem melhora econômica. |
| Distress | Liquidez corrente $AC/PC$ | **Decrescente** | Central. Cobertura contábil do passivo circulante. Estoques, recebíveis, restrições e desencontro de vencimentos limitam a interpretação. |
| Distress | Patrimônio líquido sobre ativos $PL/A_1$ | **Decrescente** | Central. Financiamento patrimonial do ativo. Sensível a perdas, baixas contábeis e outras mudanças no patrimônio. |
| Distress | Financiamentos reportados sobre ativos $(F_C+F_L)/A_1$ | Crescente | Central com escopo restrito. Peso da rubrica reportada no balanço. |
| Distress | Financiamentos circulantes sobre caixa $F_C/C$ | Crescente para $C>0$ | Complementar. Pressão dos financiamentos de curto prazo sobre o caixa. Sensível ao caixa mínimo, restrições de uso e fontes de recursos fora do balanço. |

Os agregados $F_C$ e $F_L$ podem omitir outros passivos onerosos. Debêntures, arrendamentos e outras obrigações exigem conciliação com subcontas e notas para ampliar a cobertura sem dupla contagem. A cobertura de juros fica em diligência até obter juros brutos comparáveis. O caixa operacional segue a classificação da DFC e a classificação de fluxos e saldos precisa ser preservada ao comparar pares. [CPC 03 — Demonstração dos Fluxos de Caixa](https://www.cpc.org.br/CPC/Documentos-emitidos/Pronunciamentos/Pronunciamento?Id=34) · [CPC 26 — Apresentação das Demonstrações Contábeis](https://www.cpc.org.br/CPC/Documentos-Emitidos/Pronunciamentos/Pronunciamento?Id=57)

### Redundância econômica

Com a mesma definição de receita e de ativo médio, $E/\bar A=(E/V_t)(V_t/\bar A)$ sempre que $V_t>0$ e $\bar A>0$. Dar o mesmo peso à margem, ao giro e à rentabilidade aumenta a influência do mecanismo comum. Margem e geração de caixa também compartilham a receita. No Distress, $F_C$ participa das duas razões de financiamento. Quando a identidade patrimonial se verifica e $L$ são os passivos, $(F_C+F_L)/A_1=1-PL/A_1-(L-F_C-F_L)/A_1$. Assim, financiamento e solvência podem repetir parte da informação, e $C$ e $F_C$ também influenciam a liquidez corrente pelos totais circulantes. A dependência entre os eixos pode ser econômica ou surgir de denominadores compartilhados e da seleção da amostra. A especificação mantém a independência da construção de cada eixo.

Use a identidade em casos completos como controle de coerência e reporte Pearson, Spearman, número de observações pareadas e número de emissores únicos por recorte. Uma associação elevada motiva revisão da variável, de seu papel ou de seu peso, com comparação na mesma amostra. A correlação linear dos dados brutos é mais sensível aos extremos, e a correlação dos postos pode evidenciar associação monotônica. Uma estimativa agregada em vários anos descreve as observações reunidas, com emissores que reaparecem. Inferência futura exige preservar a dependência por emissor e por período.

## Elegibilidade contábil e cobertura

| Situação | Regra proposta para reprodução |
| --- | --- |
| Consolidado | O benchmark usa `ESCOPO=con` e `GRUPO_SETORIAL=nao_financeira`, com entrega inequívoca, setor compatível e contas validadas. Uma conta individual fica no seu próprio escopo. O consolidado representa o grupo econômico. [CPC 36 — Demonstrações Consolidadas](https://www.cpc.org.br/CPC/Documentos-Emitidos/Pronunciamentos/Pronunciamento?Id=67&lang=pt) |
| Sem dados consolidados | Teste um benchmark individual separado, com pares `ind`, quando o consolidado estiver ausente na fonte e o individual passar suas próprias regras. Separe a ausência documental de um consolidado dos casos com contas consolidadas insuficientes ou com conflito de processamento. Uma falha de componente em `con` mantém a referência consolidada incompleta. |
| Holdings | Use o prefixo cadastral `Emp. Adm. Part. - ` no rótulo `SETOR_FCA` para o diagnóstico de participação. No benchmark, holdings consolidadas com setor principal não financeiro verificável podem ser elegíveis com contas compatíveis. Compare a exclusão dessas holdings como cenário. Holdings sem setor principal identificável e holdings na série individual devem aguardar protocolo próprio. Equivalência patrimonial, dividendos, estrutura de caixa e perímetro do grupo pedem diligência. |
| Exercícios | Fluxos de 365 ou 366 dias, com datas inicial e final iguais quando combinados. O comparativo de receita exige exercícios contíguos, e o saldo inicial de ativo deve anteceder o início do fluxo em um dia. Marque exercício incompatível no indicador dependente. Saldos de fechamento compatíveis continuam disponíveis para análise financeira própria. |
| Denominadores | A divisão exige denominador observado e estritamente positivo. Diferencie zero explícito, negativo, ausência e conflito contábil. Denominadores pequenos e positivos geram sinalização para auditoria e teste de sensibilidade. Preserve a razão original e a justificativa de eventual exclusão. |
| Caixa zero | Se $C=0$ e $F_C>0$, marque `caixa_zero_com_financiamento` e mantenha a razão complementar indisponível. Se $C=0$ e $F_C=0$, marque `caixa_zero_sem_financiamento_reportado` e mantenha $0/0$ indefinido. Sem evidência de $F_C$, marque a ausência separadamente. O marcador acompanha o diagnóstico sem substituição por infinito, epsilon ou percentil máximo. |
| Patrimônio líquido negativo | Preserve $PL/A_1<0$ quando o saldo e $A_1>0$ passarem os controles contábeis. Acrescente o marcador `patrimonio_liquido_negativo`. A direção negativa da razão no eixo eleva o estresse relativo. O marcador permanece visível mesmo se os demais componentes bloquearem o eixo. |
| Extremos | Verifique sinais, rótulos, unidade, ligações e coerência de período. Preserve extremos plausíveis para o benchmark de percentis. Teste a winsorização em separado, com limites estimados na amostra de referência admissível e com contagem das observações afetadas. Valores incompatíveis seguem a regra de validação aplicável. |
| Setores pequenos | Conte pares elegíveis únicos por indicador no escopo, excluindo o emissor alvo da referência de produção. Abaixo do mínimo, só use um macrosetor contábil comparável com mapeamento versionado e aprovado. Se a referência continuar insuficiente, deixe o componente indisponível por tamanho da coorte. |
| Dados sem evidência de divulgação | Classifique como `descritivo_revisado`. A publicação ou interpretação prospectiva pede evidência da disponibilidade dos insumos, versões da DFP e classificação do FCA até a data de corte. `DT_RECEB` e `DT_COLETA_DFP` registram datas distintas. [Inventário temporal da CVM](historico-dfp.md) |

Um componente é elegível se tem `SITUACAO=valido`, conta e razão verificáveis e referência de normalização admissível. Use `SITUACAO` e `DETALHE` como primeira falha da pipeline da Sprint 02. Para medir todos os denominadores físicos ausentes, zero ou negativos, revise as linhas de origem, já que um erro prévio pode impedir que o denominador seja examinado no cálculo. Um eixo exige **todos os seus componentes centrais**. O Quality pode ficar elegível com dois componentes mesmo quando um complementar falta. O Distress pode ficar elegível com três componentes mesmo quando o caixa zero impede a razão complementar. A cobertura de 4/5 Quality, 3/4 Distress, ou todos os candidatos serve a experimentos de disponibilidade e não ativa cálculo sob composição variável. Preserve o emissor no denominador documental quando um eixo falhar e informe cada impedimento verificável. Substituir uma métrica pelo valor zero, pela mediana, por outra conta, ou renormalizar os pesos na ausência de um componente mudaria o conteúdo do eixo e fica fora da proposta.

## Normalização e data de corte

Seja $X_{ij}$ a razão do emissor $i$ para o indicador $j$, e $s_j$ igual a $+1$ para direção crescente e $-1$ para decrescente. Use $Y_{ij}=s_jX_{ij}$. Uma referência aprovada $\mathcal R_j$ tem $n_j$ emissores distintos, com uma razão orientada $r_{kj}$ por emissor $k$. O percentil empírico proposto usa o ponto médio dos empates e conta todos os emissores com o mesmo valor.

$$
P_j(y\mid\mathcal R_j)=\frac{100}{n_j}\bigl(\#\{k:r_{kj}<y\}+\tfrac12\#\{k:r_{kj}=y\}\bigr).
$$

O percentil fica entre 0 e 100, preserva ordem e empates e reduz a influência da magnitude de caudas. A transformação descarta distâncias em unidades contábeis, pode saturar fora da distribuição e se torna discreta com poucos pares. Uma referência constante fica indisponível por ausência de dispersão. Preserve a razão original e o tamanho da referência. Um limiar piloto de **30 pares únicos por indicador** reduz a granulação, sem garantir precisão. Nos testes desta sprint, os limiares de 15, 30 e 50 pares mostram perda de cobertura quando o mínimo aumenta. A primeira referência proposta é o `SETOR_FCA` exato e o mesmo escopo, conservando a identificação de holding. Um macrosetor pré-aprovado oferece segunda opção comparável, devidamente identificada. A referência ampla não financeira pode servir como cenário exploratório de efeito do agrupamento. O efeito dessa troca deve ser relatado separadamente por setor e por ano, inclusive perda de elegibilidade. [Sensibilidade da cobertura aos tamanhos de referência](sprint-03a-normalizacao.md)

| Método de sensibilidade | Definição e limites |
| --- | --- |
| Z-score | $z=(y-\mu_{\mathcal R})/\sigma_{\mathcal R}$, com desvio padrão populacional da referência. Preserva a distância linear padronizada. Média e desvio são sensíveis a caudas e choques. Desvio zero produz componente indefinido. |
| Padronização robusta | $z_R=(y-\mathrm{mediana}_{\mathcal R})/d_{\mathcal R}$, com $d=1{,}4826\,\mathrm{MAD}$ e $d=\mathrm{IQR}/1{,}349$ se o MAD for zero e a IQR positiva. Escala zero nos dois casos deixa a padronização indefinida. A distância do extremo permanece interpretável em unidades robustas. Empates e grande concentração no zero podem comprimir a referência. [NIST — Medidas de dispersão](https://itl.nist.gov/div898/handbook/eda/section3/eda356.htm) |
| Normalização setorial | Define a população da referência antes da transformação escolhida, com setor, escopo, vintage e regra de amostra. Ajuda a isolar diferenças estruturais. Pode capturar ajuste à posição relativa em um setor em crise, e sinais relativos de setores distintos podem ter níveis contábeis diferentes. |

Para comparar sensibilidades na mesma escala, $100\Phi(z)$ e $100\Phi(z_R)$ podem acompanhar o percentil. $\Phi$ é a distribuição normal padrão e aqui funciona como transformação monotônica. A distância em pontos é efeito da calibração, sem significado probabilístico de um evento. Use perturbações de caudas, cortes empíricos de 1% e 99% no conjunto de referência e mudança da população setorial como cenários separados e reportados com tamanho amostral.

Em uma aplicação histórica aprovada, cada data de corte $T$ usa apenas insumos com evidência de divulgação disponível até $T$, inclusive versão das contas e informação setorial. Quando houver somente data civil verificável, considere disponibilidade a partir do início do dia seguinte no horário de Brasília. Congele o conjunto de pares e seus parâmetros antes de avaliar alvos do período. Uma janela inicial a testar é a coorte comparável do exercício anterior. A referência contém uma observação admissível por emissor. Para cada par, escolha a versão pública mais recente até o fechamento da referência, com exclusão por ambiguidade e sem reaproveitar valores de versões conhecidas somente depois do corte. Registre $T$, data de congelamento, período, escopo, setor, método, versões e hashes das fontes. A comparação contemporânea ou defasada aplicada às capturas revisadas desta sprint mede somente sensibilidade descritiva. [Metodologia temporal](metodologia.md) · [Experimentos de normalização](sprint-03a-normalizacao.md)

## Fórmulas propostas, pesos e confiabilidade

Defina $Q_1=P(E/\bar A)$, $Q_2=P(O/V_t)$, $D_1=P(-AC/PC)$, $D_2=P(-PL/A_1)$ e $D_3=P((F_C+F_L)/A_1)$, com a referência própria de cada componente. Todos os componentes já estão orientados no sentido do eixo. Para observações elegíveis e após aprovação, o benchmark de pesos iguais seria

$$
S_Q=\tfrac12 Q_1+\tfrac12 Q_2,\qquad S_D=\tfrac13 D_1+\tfrac13 D_2+\tfrac13 D_3.
$$

| Cenário fixo | Quality | Distress |
| --- | --- | --- |
| Pesos iguais centrais | 50% retorno operacional e 50% caixa operacional | Um terço para cada dimensão. |
| Alternativa econômica | 60% retorno e 40% caixa. Testa a prioridade à rentabilidade dos ativos quando o caixa em um exercício está sujeito a liberação temporária de giro. | 40% liquidez, 40% solvência e 20% financiamento reportado. Reduz o peso da exposição parcial e a possível sobreposição contábil com solvência. |
| Pesos iguais em todos os candidatos | 20% para cada indicador somente em casos completos, para testar o efeito dos complementos e da redundância. | 25% para cada indicador somente em casos completos, para testar a informação adicional de curto prazo e penalidades de seleção. |

Com componentes fixos na escala de 0 a 100, o efeito da alternativa econômica no Quality é $0{,}10(Q_1-Q_2)$, de até 10 pontos em valor absoluto. No Distress, o efeito é $(D_1+D_2-2D_3)/15$, de até 13,33 pontos. O cenário de pesos iguais em todos os candidatos também muda os componentes e a população elegível. Avalie seus efeitos na interseção das amostras antes de comparar a cobertura de cada cenário. Esses limites teóricos orientam o teste de pesos sem calcular valores por empresa nesta sprint.

A análise de pesos usa alternativas fixas na mesma amostra e preserva a independência entre os eixos. Os complementos têm peso zero no benchmark central. Qualquer versão metodológica registra os pesos antes da avaliação fora da amostra. Validação prospectiva exige resultados datados, definição de população em risco, horizonte e censura, divisões cronológicas, parâmetros congelados e avaliação de estabilidade por ano, setor e escopo.

Para cada eixo, divulgue a cobertura ponderada $c=\sum_j w_j I_j$, com $I_j=1$ para componente central elegível e $0$ nos demais casos, a lista de faltantes, os marcadores econômicos e o estado temporal. Para eixos calculáveis com todos os centrais disponíveis, proponha o indicador operacional de confiabilidade

$$
R=100c\,\min(1,n_{\min}/60)\,h,\qquad n_{\min}=\min_{j\text{ central}} n_j.
$$

Use $h=1$ para todas as referências no setor exato e $h=0{,}8$ se algum componente usar macrosetor homologado. O teto de 60 pares e o fator 0,8 são convenções preliminares de transparência e precisam de revisão. Registre a referência escolhida em cada componente e indique os casos em que coexistam referências setoriais e de macrosetor. Para eixos bloqueados, publique o diagnóstico de cobertura e a regra impeditiva, com $R$ e $S$ ausentes. A evidência temporal permanece uma condição separada de admissibilidade. $R$ descreve completude e suporte da referência, sem significar precisão estimada nem probabilidade. Os scores hipotéticos pertencem a $[0,100]$ e só admitem comparação com método, período, escopo e referência explícitos. A leitura absoluta requer as contas e razões originais.
