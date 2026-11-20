# Inventário DFP de 2019 a 2025 e disponibilidade temporal

As sete capturas oficiais foram coletadas em 20 de novembro de 2026. Cada arquivo foi processado em 11 membros, abrangendo índice de entregas e BPA, BPP, DRE, DFC-MD e DFC-MI individuais e consolidados. O manifesto de cada ano inventaria os demais membros, registra a data de coleta e permite verificar os hashes. [Catálogo DFP](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp) · [Arquivos anuais da CVM](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/)

| Ano | Registros no índice | Chaves de versão distintas | Chaves máximas com fatos | Chaves anteriores sem fatos | Linhas contábeis |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2019 | 816 | 816 | 671 | 145 | 527.330 |
| 2020 | 891 | 891 | 733 | 158 | 593.180 |
| 2021 | 947 | 946 | 771 | 175 | 623.525 |
| 2022 | 935 | 935 | 731 | 204 | 634.790 |
| 2023 | 893 | 892 | 733 | 159 | 647.921 |
| 2024 | 873 | 872 | 709 | 163 | 623.646 |
| 2025 | 761 | 761 | 671 | 90 | 596.121 |

Nas sete capturas, os fatos publicados correspondem a chaves de versão máxima do índice. Há 1.094 chaves de versões anteriores presentes apenas no índice. Também há casos com apenas uma versão registrada. O índice fornece evidência do registro de uma versão e sua data de recebimento. A primeira versão registrada com fatos atuais só representa os valores da primeira entrega quando a versão foi vinculada de modo inequívoco. A divulgação efetiva desses valores na época requer evidência própria.

## Reprodução da captura

| Ano | SHA-256 do ZIP DFP | Último recebimento no índice |
| --- | --- | --- |
| 2019 | `bc82a1162b44686e8953b521e3424a5938b6661ff4655f832db4ea9488296a0d` | 2022-05-26 |
| 2020 | `8fb97d1887aed1e1e2d85e54cb133baf9f65b9f46f60fa8720f09c1f7a74362e` | 2024-12-23 |
| 2021 | `64b8693b709538a0357c5179ae02231cb380d0000956ee57a873a21d4efda2e4` | 2024-12-23 |
| 2022 | `0cdb73c0aa57a68e8b2c2d0a0b4a1a3ccce359f16c2964fde656f9624de9a6a4` | 2024-12-23 |
| 2023 | `5748ee4e9f1c8cd428931050e9da2ead174ad737af11d842a50d7bad8064145b` | 2026-03-31 |
| 2024 | `0a1e41edc81900df6605448acb2fcf6fae36f9a8ac4756a7d658cd7c718a1501` | 2026-04-17 |
| 2025 | `6b24bc65a614605e2c1e45ae1fa237ebbe72672467e87f7761cca94f3e6bc040` | 2026-11-05 |

Para repetir a análise após atualizações do portal, use os ZIPs arquivados com `--arquivo` e `--sha256`. `python -m quantdistress.data.history` aceita os caminhos das capturas processadas, verifica os Parquet e produz as contagens de versões em JSON.

Os hashes das fontes cadastrais coletadas em 20/11/2026 também constam do manifesto do painel. [Arquivos FCA](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/) · [Cadastro atual](https://dados.cvm.gov.br/dataset/cia_aberta-cad)

| Fonte cadastral | SHA-256 |
| --- | --- |
| FCA 2019 | `09f84e5f5485217c8b36f8379c36f718dbdcd6d6908b4e96b68861394e76fe97` |
| FCA 2020 | `ccf2ac081747da9ccefa50349a5494c263763d5dd8bb961565fd2ae64c264b20` |
| FCA 2021 | `65ba4b0225e9b2106901cdf348215933be8affba79925fc71361e2f6818c7999` |
| FCA 2022 | `a5afd93f7b4ff8694b35c584163d27764b7de8adbb2bb80873325df0dfb22337` |
| FCA 2023 | `292b64f25a3c473c138d95687cb0088a7d1e55d235cb65f744b71911af284f29` |
| FCA 2024 | `169e209876b9e1c11568019e74bbd1b9a4cfc91d37b361b1138ab43707c96cbe` |
| FCA 2025 | `b7d2e3b98b99e9e595efa0d3575cd40a55c5dbf15d8d4087c5c3f4afec08f1d4` |
| Cadastro atual | `bfa32041402a430b8cc1e5237d377554035369f511d0c9c2169a0182b4105d8c` |

Nos CSVs BPP individuais e consolidados de 2019 e 2020, a descrição `"Senior Notes" Reestruturados` tinha aspas literais sem o escape exigido pelo CSV. O leitor aplica uma correção delimitada a esse campo, preserva o texto decodificado e registra os oito registros reparados no manifesto. O ZIP original permanece intacto. Demais erros de estrutura continuam bloqueando o processamento. [Teste da compatibilidade](../tests/test_historico_dfp.py)

## Recuperação documental pelo Empresas.NET

A CVM informa que sua consulta externa permite recuperar reapresentações, e a nota de download múltiplo descreve formatos XML de formulários e o acesso mediante cadastro. O índice DFP fornece `ID_DOC`, data de recebimento e `LINK_DOC` por entrega, inclusive anteriores à versão máxima. [Consulta pública do Empresas.NET](https://www.rad.cvm.gov.br/enetconsulta/frmGerenciaPaginaFRE.aspx) · [Histórico de versões na consulta](https://www.gov.br/cvm/pt-br/assuntos/noticias/2019-1/nova-versao-do-empresasnet-moderniza-busca-por-informacoes-de-companhias-abertas-59dc2c429727468ba15e85b54661ab5e) · [Nota técnica do download múltiplo](https://www.gov.br/cvm/pt-br/assuntos/regulados/consultas-por-participante/companhias/download-multiplo-de-documentos-periodicos-e-eventuais/nota-tecnica-sobre-o-download-multiplo-de-informacoes-sobre-companhias)

Uma sondagem do código CVM `023981` encontrou um pacote ZIP pelo `LINK_DOC` da versão 1 de 31/03/2019 (`ID_DOC` `85068`), contendo o XML de demonstrações `FormularioDemonstracaoFinanceiraDFP.xml`. A versão 2 está indexada como `85079`. Esta segunda consulta excedeu o tempo de resposta. Para a referência de 31/03/2024, a versão 1 (`137782`) respondeu HTTP 200 sem arquivo DFP e a tentativa da versão 3 (`142069`) excedeu o tempo. Os resultados demonstram possibilidade de recuperação pontual e mostram por que o status HTTP isolado é insuficiente. [Pacote da versão anterior 85068](https://www.rad.cvm.gov.br/ENETCONSULTA/frmDownloadDocumento.aspx?CodigoInstituicao=1&NumeroSequencialDocumento=85068)

Para ampliar a recuperação, a equipe deve guardar o arquivo e seu hash, vincular a identidade interna e externa da entrega, mapear contas e escopos do documento para o modelo DFP e medir cobertura por ano e versão. A consulta ou sua documentação precisa sustentar a data em que a informação passou a estar efetivamente disponível. A sondagem desta sprint ainda carece de extração de contas em escala, cobertura documental e validação de divulgação suficientes para backtesting.

## Semântica das datas

| Campo | Significado no painel |
| --- | --- |
| `DT_REFER` | Data de referência contábil da DFP. `DT_INI_EXERC` e `DT_FIM_EXERC` especificam os intervalos ou saldos das linhas correntes e comparativas. |
| `DT_RECEB` | Data de recebimento pela CVM no índice, associada apenas a uma entrega inequivocamente identificada. |
| `DT_DIVULGACAO` | Data de disponibilidade pública do conteúdo. Permanece ausente quando a evidência ainda está em diligência. |
| `DT_COLETA_DFP` | Data e hora UTC de aquisição da captura anual. As datas declaradas para a coleta de FCA e cadastro ficam no manifesto. |
| `VERSAO` | Número da versão do formulário. A versão usada na camada analítica é selecionada com a informação disponível na captura de 2026. |

O painel recebe o modo `descritivo_revisado`. A separação explícita das datas e o histórico no índice preservam as evidências necessárias para uma futura camada de informação disponível em cada corte. [Metodologia temporal](metodologia.md)
