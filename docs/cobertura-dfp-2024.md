# Cobertura e limitações das DFP de 2024

ImpactUFSCar — Área de Pesquisa & Mercado

## Fonte e reprodução

O pipeline baixou o ZIP oficial de DFP de 2024 em 20 de novembro de 2026, às 09h23min47s no horário de Brasília. O ZIP tem 13.397.608 bytes e o SHA-256 é `0a1e41edc81900df6605448acb2fcf6fae36f9a8ac4756a7d658cd7c718a1501`. O manifesto local registra membros processados, membros inventariados e hashes dos Parquets. A CVM atualiza o conjunto com reapresentações, portanto a URL pode fornecer outro snapshot em uma execução futura. [Catálogo DFP da CVM](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp) · [ZIP oficial de 2024](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_2024.zip)

```sh
uv sync --locked
uv run --locked quantdistress-dfp --ano 2024 --sha256 0a1e41edc81900df6605448acb2fcf6fae36f9a8ac4756a7d658cd7c718a1501
uv run --locked jupyter nbconvert --to notebook --execute notebooks/01_exploracao_dfp.ipynb --output-dir outputs
```

Se o catálogo já servir outro ZIP, execute o pipeline com `--arquivo CAMINHO` e o SHA-256 acima para reproduzir esta análise a partir de uma cópia local do snapshot. Se houver vários snapshots na pasta anual, configure `QUANTDISTRESS_DFP_SNAPSHOT` com o diretório escolhido. A execução do notebook verifica os hashes dos Parquets e as contagens declaradas no manifesto.

## Cobertura observada

Foram processados 11 dos 19 CSVs do ZIP, abrangendo o índice de entregas e dez arquivos de balanços, DRE e DFC. Os oito arquivos de DMPL, DRA, DVA, composição do capital e pareceres estão inventariados no manifesto. O Parquet de fatos tem **623.646 linhas**. O índice tem **873 registros** de **709 emissores** identificados por código CVM e **872 chaves distintas** de CNPJ, código CVM, data de referência e versão.

| Demonstração | Linhas consolidadas | Chaves consolidadas | Linhas individuais | Chaves individuais |
| --- | ---: | ---: | ---: | ---: |
| BPA | 62.680 | 467 | 94.515 | 704 |
| BPP | 107.116 | 467 | 159.522 | 704 |
| DRE | 32.776 | 467 | 46.294 | 704 |
| DFC — método direto | 656 | 16 | 856 | 23 |
| DFC — método indireto | 50.674 | 451 | 68.557 | 681 |
| Total de linhas | **253.902** | | **369.744** | |

Das 872 chaves do índice, **467 consolidadas (53,6%)** e **704 individuais (80,7%)** têm BPA, BPP, DRE e uma DFC para o último exercício. Em cada escopo, as chaves com fatos têm cobertura dos quatro blocos e um único método de DFC. A interseção conta 462 chaves e a união conta 709, com uma chave por emissor. Sobre as 709 chaves de versão máxima, a cobertura dos quatro blocos é de 65,9% no consolidado e 99,3% no individual. A presença de uma demonstração é apenas uma das condições para usar suas contas em um indicador.

## Datas, reapresentações e comparabilidade

- O índice contém 710 registros da versão 1, 139 da versão 2, 22 da versão 3 e 2 da versão 4. Há 139 chaves de emissor e data com mais de uma versão. Em ambos os escopos, todas as chaves com fatos são da **versão máxima por emissor e data no índice**. As 163 chaves de versões inferiores aparecem apenas no índice. A seleção de uma versão pelo corte temporal, sozinha, não recupera os valores contábeis ausentes desse ZIP.
- As datas de referência vão de 28 de fevereiro a 31 de dezembro de 2024, com 861 dos 873 registros em 31 de dezembro. O recebimento registrado vai de 9 de maio de 2024 a 17 de abril de 2026. O índice tem 11 registros com recebimento em 2024, 850 em 2025 e 12 em 2026. Uma avaliação temporal requer verificar a data em que o conteúdo se tornou público e reunir versões disponíveis em cada corte.
- Há 312.171 linhas do último exercício e 311.475 linhas comparativas. Nas linhas do último exercício, o fim do exercício coincide com a referência da entrega. A mesma entrega pode conter períodos comparativos de duração diferente. Nos fluxos, 50 combinações distintas de chave, escopo, família, ordem e período duram menos de 365 dias, entre 31 e 354 dias, sem datas de início ou fim ausentes. Métricas de crescimento e de giro exigem regras de comparabilidade antes de combinar períodos.
- Todas as linhas processadas informam `REAL`, sendo 609.456 na escala `MIL` e 14.190 em `UNIDADE`. O texto decimal original preserva a precisão declarada. Indicadores que usam valores em dinheiro precisam aplicar a escala após validar a natureza da conta. Valores por ação exigem uma regra específica.

## Integridade e conciliação

- Os 623.646 fatos têm vínculo único com o índice. O índice contém uma chave repetida com dois identificadores e datas de recebimento diferentes. Essa chave não ocorre nos fatos deste snapshot. O pipeline retém os registros, sinaliza o conflito e exige vínculo único para anexar os metadados de um documento.
- **7.270 linhas** pertencem a grupos com chave de fato repetida e **7.236** pertencem a grupos de linhas exatamente repetidas. Os totais contam todas as linhas dos grupos, incluindo a primeira ocorrência. Ambos os tipos ficam sinalizados e preservados. A ausência de nulos em `VL_CONTA` e de escalas desconhecidas neste snapshot não implica completude econômica.
- A conciliação patrimonial comparou o total do ativo (`BPA 1`) ao total do passivo e patrimônio líquido (`BPP 2`) na mesma chave, escopo e período. Para esse teste, totais repetidos com o mesmo valor monetário, escala e moeda participam uma vez, preservando todas as linhas nas tabelas. A tolerância foi uma unidade da maior escala de publicação de cada par. A diferença foi exatamente zero nos **934 pares consolidados** e **1.407 individuais**, incluindo comparativos. Esse teste cobre a identidade dos totais e deixa em aberto a consistência dos componentes.

## Implicações para os indicadores

| Eixo candidato | Evidência no último exercício consolidado | Pendência de padronização |
| --- | --- | --- |
| Qualidade operacional | DRE `3.05` tem o rótulo “Resultado Antes do Resultado Financeiro e dos Tributos” em 448 de 467 chaves e outros conceitos em 19. A DFC `6.01` aparece nas 467 chaves com variações de rótulo. | Validar receita, resultado operacional, fluxo de caixa e capital investido por layout e setor. Verificar a equivalência dos métodos de DFC e o efeito da duração dos exercícios. |
| Estresse financeiro | Balanços `1.01` e `2.01` trazem “Ativo Circulante” e “Passivo Circulante” em 450 de 467 chaves. Nas outras 17, os códigos identificam caixa e passivos financeiros a valor justo, respectivamente. `2.03` também varia entre patrimônio líquido, provisões e passivos financeiros. | Mapear liquidez, dívida, despesa financeira e patrimônio líquido por conceito e setor. Tratar denominador inválido, dívida de curto prazo indisponível e ausência de demonstração como condições distintas. |

O recorte cobre as entregas de um único pacote anual e sua posição em novembro de 2026. A amostra analítica precisa de um universo histórico de emissores, inclusive empresas que deixaram de reportar, e de eventos datados para avaliar o risco de viés de sobrevivência e vazamento de informação. Consulte a [metodologia](metodologia.md) e as [pendências da Sprint 02](sprint-02.md).
