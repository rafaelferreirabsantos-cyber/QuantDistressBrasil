# Metodologia de pesquisa

QuantDistress Brasil é um projeto acadêmico e não comercial da ImpactUFSCar, pela Área de Pesquisa & Mercado, na Universidade Federal de São Carlos, campus Sorocaba. A área responde pela pesquisa, desenvolvimento, validação, documentação e evolução do projeto.

## Pergunta e hipótese

Entre companhias abertas brasileiras sob estresse financeiro, a qualidade da operação varia de forma mensurável? Essa variação acrescenta informação sobre a trajetória futura das empresas em relação a uma análise baseada apenas na pressão financeira?

> Empresas sob estresse financeiro podem preservar diferentes níveis de qualidade operacional, e essa distinção pode fornecer informação relevante para análise de distress, recuperação empresarial e Special Situations.

A hipótese é associativa. Uma empresa pode reportar margens e geração operacional de caixa relativamente fortes e, no mesmo período, enfrentar baixo caixa disponível e vencimentos concentrados. O estudo precisa verificar se as diferenças persistem por setor, período e escolha dos indicadores. Cada empresa observada entra no universo a partir de regras cadastrais e de disponibilidade definidas para a data de análise. Assim, o universo inclui emissores que saíram posteriormente da amostra de companhias ativas e permite medir a cobertura dos próprios dados.

## Unidade de análise e fontes

- A unidade contábil pretendida é emissor, exercício fiscal e escopo da demonstração. A versão do formulário acompanha a data de referência e pode se repetir em documentos com identificadores distintos. Usar o código CVM e o CNPJ informado na fonte para rastrear o emissor. Datas do formulário, datas das contas e datas de recebimento ou divulgação cumprem papéis distintos.
- O consolidado é o escopo de referência proposto para análise econômica do grupo. O individual fica preservado como escopo próprio, inclusive para examinar companhias sem consolidado. Uma métrica usa um único escopo e versões compatíveis entre demonstrações. Uma análise com individuais deve explicitar a população elegível e comparar sua cobertura à do consolidado.
- A Sprint 01 processa o índice de entregas DFP e as demonstrações BPA, BPP, DRE, DFC-MD e DFC-MI nos escopos consolidado e individual. As demais famílias ficam inventariadas. O recorte preserva versões e linhas comparativas presentes no arquivo. Arquivo original, URL de origem, data de coleta e hash sustentam a reprodução de uma execução. [CVM | DFP](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp)
- O ITR pode apoiar estudos de frequência trimestral posteriores, com convenções próprias de períodos e acumulação. O IPE é fonte candidata para identificar e verificar eventos como recuperação judicial e falência. A curadoria deve distinguir o evento inicial de comunicados de acompanhamento e guardar a fonte utilizada para cada decisão. [CVM | ITR](https://dados.cvm.gov.br/dataset/cia_aberta-doc-itr) · [CVM | IPE](https://dados.cvm.gov.br/dataset/cia_aberta-doc-ipe)

## Eixos de análise propostos

Cada eixo terá escala de 0 a 100. Valores maiores do **Quality Score** indicarão maior qualidade econômica e operacional. Valores maiores do **Financial Distress Score** indicarão maior pressão financeira. Os eixos terão construção e interpretação próprias e formarão uma matriz bidimensional. É possível haver correlação empírica entre eles. As escalas representam medidas relativas segundo regras documentadas de normalização e cobertura. A leitura conjunta serve à pesquisa e à análise contextual de casos.

| Eixo | Dimensão candidata | Medida a estudar e condição de uso |
|---|---|---|
| Quality | Rentabilidade operacional | Resultado operacional ÷ ativos médios, com saldos no início e no fim do período do resultado. |
| Quality | Margens | Resultado operacional ÷ receita líquida, em setores com definição de receita comparável e denominador positivo. |
| Quality | Geração de caixa | Fluxo de caixa operacional ÷ receita líquida, conciliando a disponibilidade do agregado entre DFC direta e indireta. |
| Quality | Eficiência do capital | Receita líquida ÷ capital empregado médio, após definir as contas de capital empregado e os critérios para denominadores válidos. |
| Quality | Crescimento e estabilidade | Crescimento de receita em períodos de duração comparável e dispersão histórica de margens em janela e cobertura mínimas predefinidas. |
| Distress | Alavancagem | Dívida financeira bruta ÷ ativos, com composição de dívida explícita e tratamento documentado de arrendamentos. |
| Distress | Liquidez | Ativo circulante ÷ passivo circulante, com condição mínima para denominador e mapeamento aplicável ao setor. |
| Distress | Serviço da dívida | Resultado operacional ÷ despesa financeira bruta ou, onde houver dados confiáveis, fluxo de caixa disponível ÷ juros e amortizações. Os conceitos exigem testes de viabilidade separados. |
| Distress | Solvência | Patrimônio líquido ÷ ativos, investigando separadamente situações de patrimônio líquido negativo. |
| Distress | Pressão de curto prazo | Dívida financeira circulante ÷ caixa e equivalentes, com estados distintos para caixa igual a zero e caixa ausente. |

As expressões são candidatas ao diagnóstico de viabilidade. Contas, critérios de validade, limites de cobertura, pesos e referências de escala serão definidos com base na análise de dados e na validação temporal. A direção de cada indicador precisa ser explícita. Maior liquidez, por exemplo, reduz a pressão estimada quando a razão é aplicável. Variáveis que compartilham contas entre os eixos exigem diagnóstico de redundância. Um caso com ambos os valores altos pode fundamentar uma análise contábil aprofundada. A interpretação da viabilidade e da recuperação depende de evidências adicionais sobre caixa, financiamento e evolução operacional.

## Contabilidade, setores e qualidade dos dados

1. **Período.** Balanços registram saldos em uma data. DRE e DFC medem fluxos durante um intervalo. Verificar as datas inicial e final antes de construir comparações anuais. Identificar exercícios curtos ou longos e mudanças de encerramento. Comparativos reapresentados em um formulário posterior se tornam elegíveis na data de disponibilidade daquele formulário.
2. **Hierarquia e escala.** Mapear conta, demonstração, escopo, sinal, moeda e escala numérica. Selecionar o total ou os componentes elegíveis e justificar a seleção para evitar dupla contagem. Manter valores originais e sua unidade para reconciliar conversões e explicar diferenças de arredondamento. Confirmar a unidade de cada conta antes de aplicar a escala declarada no formulário. Valores por ação na DRE exigem tratamento próprio.
3. **Consistência.** Conciliar, quando aplicável, ativos totais com a soma das obrigações e do patrimônio líquido, e verificar continuidade dos saldos, períodos e abrangência dos totais. Registrar regras, tolerâncias compatíveis com a escala, incidências e razões para exclusões. Preservar ocorrências de origem para diagnóstico.
4. **Cobertura e faltantes.** Distinguir valor reportado igual a zero, conta ausente, dado não aplicável ou indisponível, erro de validação e denominador impróprio. Medir cobertura por ano, setor, escopo e indicador. Estabelecer cobertura mínima para combinar dimensões. Quantificar o efeito de exclusões e testar a sensibilidade a tratamentos de dados faltantes.
5. **Setores e caudas.** Definir grupos de comparação a partir de classificação historicamente disponível. Instituições financeiras e seguradoras requerem mapeamentos e critérios próprios para capital, liquidez e fluxos. Distinguir extremos economicamente plausíveis de erros de extração. Quando necessário, estimar cortes robustos ou limites de winsorização apenas na amostra de desenvolvimento e testar o efeito de preservar os valores originais.

## Disponibilidade e validação temporal

Antes da seleção de uma versão para qualquer data de corte, estabelecer quando aquela entrega ficou publicamente disponível. A data de recebimento pela CVM pode servir como aproximação documentada quando sua relação com a divulgação estiver sustentada por evidência. Se a divulgação for conhecida apenas no nível de dia, considerar disponibilidade a partir do início do dia seguinte. Excluir do painel histórico entregas sem evidência temporal suficiente e registrar o efeito sobre a cobertura. A data de download identifica a coleta do arquivo, e a data contábil identifica a competência ou o encerramento do exercício. [CVM | Dicionário de dados DFP](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp/resource/cbf44db1-06b8-45f7-8318-88d1564e9451)

Na data de corte, selecionar a versão elegível mais recente conforme a evidência de disponibilidade e usar apenas contas publicadas até esse ponto. Registrar datas de corte, versões e fontes das observações usadas. Quando um fato contábil se vincular a mais de uma entrega, resolver o vínculo com evidência documental antes de atribuir uma data. Arquivos atuais podem conter revisões posteriores ou cobertura incompleta de versões históricas. Avaliar essa cobertura antes de afirmar que o painel representa a informação disponível no passado.

Para avaliar associação com eventos, definir antes da estimação o evento inicial elegível, data, horizonte e regras de censura. Por exemplo, uma análise de recuperação judicial em 12 meses exige evidência da data do evento e observação suficiente do horizonte para classificar os casos sem evento observado. Empresas que já se encontravam em recuperação no corte pertencem a uma análise de evolução do estado, com critérios próprios. Incluir emissores inativos na data de extração quando eram elegíveis no corte e investigar seleção por ausência de demonstrações, saída de registro ou interrupção do acompanhamento.

Desenvolver primeiro descrições e regras interpretáveis. Separar desenvolvimento, validação e teste final em blocos cronológicos, com intervalo suficiente para que os resultados usados em desenvolvimento já estivessem observáveis no início do bloco seguinte. Fixar mapeamentos, tratamentos de faltantes e extremos, transformações e pesos antes do teste. Para examinar a hipótese, comparar uma referência de pressão financeira com uma análise que acrescente informação operacional na mesma coorte elegível. Reportar cobertura, taxas observadas por faixas, métricas adequadas a eventos raros, como a área sob a curva precisão-revocação, e incerteza que considere a repetição de emissores. A execução com a DFP de 2024 informa a qualidade e a cobertura da ingestão para aquele recorte e orienta os testes de viabilidade dos indicadores.

As prioridades e critérios de aceite para transformar esse desenho em um painel de pesquisa estão no [backlog da Sprint 02](sprint-02.md).
