# Conceitos contábeis e indicadores candidatos

Os protótipos usam o leiaute não financeiro identificado no FCA e confirmado em cada conta da DFP. As regras usam família, código, indicador de conta fixa e rótulo. Os saldos mantêm o escopo de origem. A cobertura dos protótipos informa sua viabilidade contábil no painel descritivo da Sprint 02.

## Contas validadas para os protótipos

| Conceito | Família e código | Rótulo ou distinção de escopo |
| --- | --- | --- |
| Ativo total | BPA `1` | Ativo Total |
| Ativo circulante | BPA `1.01` | Ativo Circulante |
| Caixa e equivalentes | BPA `1.01.01` | Caixa e Equivalentes de Caixa |
| Passivo circulante | BPP `2.01` | Passivo Circulante |
| Financiamentos circulantes | BPP `2.01.04` | Empréstimos e Financiamentos, ramo circulante |
| Financiamentos não circulantes | BPP `2.02.01` | Empréstimos e Financiamentos, ramo não circulante |
| Patrimônio líquido | BPP `2.03` | Patrimônio Líquido Consolidado em `con` e Patrimônio Líquido em `ind` |
| Receita | DRE `3.01` | Receita de Venda de Bens e/ou Serviços |
| Resultado antes do financeiro e tributos | DRE `3.05` | Resultado Antes do Resultado Financeiro e dos Tributos |
| Caixa operacional | DFC-MD ou DFC-MI `6.01` | Caixa Líquido Atividades Operacionais ou Caixa Líquido das Atividades Operacionais. Uma única alternativa por entrega e período |

Os rótulos aceitam diferenças de caixa e espaços. A cobertura de uma família ou código, isoladamente, é insuficiente. No piloto de 2024, layouts distintos usam códigos como BPA `1.01`, BPP `2.01` e DRE `3.05` para conceitos diferentes. As observações com grupo `financeira`, `regime_especifico` ou `nao_classificada` ficam no denominador documental e fora da população de cálculo. Os resultados `con` descrevem o grupo e os resultados `ind` descrevem a companhia individual. A interpretação de holdings individuais exige cuidado com a estrutura de suas receitas e despesas. [Cobertura DFP 2024](cobertura-dfp-2024.md)

## Protótipos e interpretação

| Eixo | Indicador | Fórmula e interpretação |
| --- | --- | --- |
| Quality | Margem operacional | Resultado DRE `3.05` ÷ receita. Mede o resultado antes do financeiro e tributos por unidade de receita. |
| Quality | Rentabilidade operacional sobre ativos | Resultado DRE `3.05` ÷ média dos ativos inicial e final. Mede o resultado em relação aos ativos contábeis empregados. |
| Quality | Fluxo de caixa operacional sobre receita | DFC `6.01` ÷ receita. Mede a conversão da receita em caixa operacional no mesmo período. |
| Quality | Giro do ativo | Receita ÷ média dos ativos inicial e final. Mede receita por unidade de ativo. O ativo contábil médio é a base do giro. |
| Quality | Crescimento da receita | Receita corrente ÷ receita comparativa − 1. Compara dois exercícios contíguos reportados na mesma versão. |
| Distress | Liquidez corrente | Ativo circulante ÷ passivo circulante. Mede cobertura contábil das obrigações circulantes, sujeita à composição do ativo. |
| Distress | Patrimônio líquido sobre ativos | Patrimônio líquido ÷ ativo total. Indica a parcela do ativo financiada por patrimônio líquido e preserva valores negativos. |
| Distress | Financiamentos reportados sobre ativos | (Financiamentos circulantes + não circulantes) ÷ ativo total. Mede a exposição dos dois agregados declarados, com cobertura dependente do leiaute e da classificação contábil. |
| Distress | Financiamentos circulantes sobre caixa | Financiamentos circulantes ÷ caixa e equivalentes. Mede pressão financeira reportada de curto prazo em relação ao caixa. |

## Validade e rastreabilidade

- Cada indicador usa uma única entrega DFP, versão e escopo, com identificação inequívoca do documento e linha de origem. Conflitos em uma conta requerida, inclusive dois métodos de DFC candidatos, bloqueiam o indicador. As demais contas e indicadores seguem sua própria avaliação. [Auditoria de duplicatas](auditoria-duplicatas.md)
- O saldo atual fecha na data de referência. Fluxos têm 365 ou 366 dias e a mesma data de início e fim quando usados na mesma razão. O ativo inicial é o saldo comparativo com fechamento no dia anterior ao início do fluxo. Crescimento exige exercícios contíguos. Comparativos pertencem ao documento que os publicou e podem refletir reapresentações.
- Todos os insumos monetários exigem `REAL` e escala `MIL` ou `UNIDADE` consistente. O cálculo transforma o decimal original em unidades monetárias. Os saldos de ativo, circulantes, caixa e financiamentos elegíveis são não negativos. Patrimônio líquido, resultado e caixa operacional admitem sinais negativos.
- Valores ausentes, denominadores nulos ou não positivos, períodos incompatíveis e sinais indevidos deixam `VALOR` nulo. Um zero reportado pode ser um numerador válido. A situação e o detalhe registram a primeira regra que impediu o cálculo. `FONTES` contém os insumos já validados, com família, conta, período, escala e valor original, número do documento, membro CSV e linha. O SHA-256 da captura acompanha a observação.
- Os testes exercitam fórmulas, escalas, sinal, denominador, validade de períodos, rótulos, conflitos e separação de escopos. O relatório apresenta os denominadores de cobertura por setor e período. [Testes dos indicadores](../tests/test_indicadores.py) · [Cobertura e parecer](resultado-sprint-02.md)

## Dimensões pendentes

| Dimensão | Evidência necessária para avançar |
| --- | --- |
| Capital empregado e retorno sobre capital | Definir a composição de capital operacional, com tratamento de participações, caixa excedente e arrendamentos. O giro de ativos é a medida restrita disponível. |
| Estabilidade operacional | Construir janelas de períodos com duração e conceitos consistentes. Validar a cobertura antes de atribuir dispersão a empresas com poucas observações. |
| Dívida onerosa completa | Conciliar empréstimos com debêntures, arrendamentos e outros passivos financeiros em notas e subcontas, controlando dupla contagem. A medida atual usa os dois agregados reportados. |
| Cobertura de juros | Obter despesa de juros bruta em classificação comparável. A despesa financeira agregada pode incluir câmbio, derivativos e itens além de juros. |
| Bancos, seguradoras e outros regimes específicos | Definir referências setoriais próprias de liquidez, alavancagem e resultado. A caixa, os ativos e os passivos desses emissores exigem interpretação compatível com seus layouts e operações. |
