# QuantDistress Brasil

Projeto de pesquisa acadêmica e não comercial da **ImpactUFSCar — Área de Pesquisa & Mercado**, Universidade Federal de São Carlos, campus Sorocaba. A área responde pela pesquisa, pelo desenvolvimento, pela validação, pela documentação e pela evolução do sistema.

O QuantDistress Brasil investiga se companhias brasileiras sob estresse financeiro preservam diferentes níveis de qualidade operacional. A pesquisa procura distinguir sinais de pressão na estrutura de capital de sinais de deterioração operacional para apoiar o estudo de recuperação empresarial e *special situations*.

O desenho prevê dois índices independentes de 0 a 100. O **Quality Score** aumenta com a qualidade econômica e operacional. O **Financial Distress Score** aumenta com o estresse financeiro. Juntos, eles formam uma matriz de classificação para pesquisa descritiva. A matriz permite selecionar casos para estudo. Estimativas de probabilidade e decisões de investimento exigem métodos e evidências próprios. As dimensões, fórmulas e regras de elegibilidade passarão por validação antes da implementação dos índices.

## Sprint 01

A primeira entrega organiza a ingestão e a exploração das demonstrações financeiras padronizadas anuais da CVM. O pipeline lê o índice de entregas e os arquivos de BPA, BPP, DRE, DFC pelo método direto e DFC pelo método indireto, cada um em seu escopo individual ou consolidado. Ele preserva exercícios correntes e comparativos, versões, identificadores e a origem de cada registro. O piloto usa a DFP 2024. ITR e IPE são fontes de pesquisa para fases posteriores. [DFP](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp) · [ITR](https://dados.cvm.gov.br/dataset/cia_aberta-doc-itr) · [IPE](https://dados.cvm.gov.br/dataset/cia_aberta-doc-ipe)

## Execução local

Execute na raiz do repositório com `uv` e Python 3.13. O `uv.lock` fixa as dependências. O grupo `dev` inclui Pytest e Jupyter. [Documentação do uv](https://docs.astral.sh/uv/)

```bash
uv sync --locked
uv run --locked pytest
uv run --locked quantdistress-dfp --ano 2024
```

O último comando baixa a versão atualmente publicada pela CVM e imprime o caminho da captura processada. O ZIP bruto fica em `data/raw/dfp/<ano>/<sha256>/`. Os arquivos `entregas.parquet`, `fatos.parquet` e `manifesto.json` ficam em `data/interim/dfp/<ano>/<sha256>/`. Guarde o ZIP e o manifesto junto com a referência do experimento. A CVM atualiza seus arquivos com reapresentações, e o mesmo ano pode gerar outro hash. Para repetir uma captura arquivada, informe o caminho do ZIP e, opcionalmente, seu hash esperado.

```bash
uv run --locked quantdistress-dfp --ano 2024 --arquivo "caminho/dfp_cia_aberta_2024.zip" --sha256 0a1e41edc81900df6605448acb2fcf6fae36f9a8ac4756a7d658cd7c718a1501
```

A suíte usa fixtures locais por padrão. Para testar a correspondência entre todos os registros publicados nos onze CSVs do escopo e os dois Parquet gerados pela CLI, habilite o teste com o ZIP oficial. No PowerShell, execute os comandos abaixo na raiz do projeto.

```powershell
$env:QUANTDISTRESS_TEST_DFP_2024 = 'caminho/dfp_cia_aberta_2024.zip'
uv run --locked pytest
```

Execute todas as células do notebook e grave uma cópia com os resultados em `outputs/`.

```bash
uv run --locked jupyter nbconvert --to notebook --execute notebooks/01_exploracao_dfp.ipynb --output-dir outputs
```

O notebook localiza a captura processada de 2024. Quando houver mais de uma captura, defina a variável de ambiente `QUANTDISTRESS_DFP_SNAPSHOT` com o caminho para a pasta que contém o manifesto e os dois arquivos Parquet. Para exploração interativa, inicie `uv run --locked jupyter lab` na raiz e abra o notebook.

## Estrutura e documentação

| Caminho | Conteúdo |
| --- | --- |
| `src/quantdistress/data/` | Aquisição, validação de estrutura, normalização e rastreabilidade da DFP |
| `src/quantdistress/evaluation/` | Diagnósticos de integridade e cobertura |
| `src/quantdistress/features/`, `src/quantdistress/scoring/` | Módulos reservados à construção e à validação futura dos indicadores |
| `data/raw/`, `data/interim/`, `data/processed/` | Capturas brutas, tabelas de ingestão e camada analítica futura |
| `notebooks/`, `tests/`, `outputs/` | Exploração, testes automatizados e resultados locais |

- [Metodologia de pesquisa](docs/metodologia.md)
- [Dicionário de dados da ingestão DFP](docs/dicionario-dados.md)
- [Cobertura e limitações da DFP 2024](docs/cobertura-dfp-2024.md)
- [Pendências da Sprint 02](docs/sprint-02.md)

O Git versiona código, configuração e documentação. Capturas brutas, Parquet, ambiente virtual e resultados gerados ficam nas pastas locais ignoradas. Fixtures sintéticas servem aos testes automatizados. O relatório de cobertura usa a captura oficial identificada por hash.
