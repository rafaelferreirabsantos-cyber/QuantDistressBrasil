# QuantDistress Brasil

Projeto de pesquisa acadêmica e não comercial da **ImpactUFSCar — Área de Pesquisa & Mercado**, Universidade Federal de São Carlos, campus Sorocaba. A área responde pela pesquisa, pelo desenvolvimento, pela validação, pela documentação e pela evolução do sistema.

O QuantDistress Brasil investiga se companhias brasileiras sob estresse financeiro preservam diferentes níveis de qualidade operacional. A pesquisa procura distinguir sinais de pressão na estrutura de capital de sinais de deterioração operacional para apoiar o estudo de recuperação empresarial e *special situations*.

O desenho prevê dois índices independentes de 0 a 100. O **Quality Score** aumenta com a qualidade econômica e operacional. O **Financial Distress Score** aumenta com o estresse financeiro. Juntos, eles formam uma matriz de classificação para pesquisa descritiva. A matriz permite selecionar casos para estudo. Estimativas de probabilidade e decisões de investimento exigem métodos e evidências próprios. As dimensões, fórmulas e regras de elegibilidade passarão por validação antes da implementação dos índices.

## Sprint 01

A primeira entrega organiza a ingestão e a exploração das demonstrações financeiras padronizadas anuais da CVM. O pipeline lê o índice de entregas e os arquivos de BPA, BPP, DRE, DFC pelo método direto e DFC pelo método indireto, cada um em seu escopo individual ou consolidado. Ele preserva exercícios correntes e comparativos, versões, identificadores e a origem de cada registro. O piloto usa a DFP 2024. ITR e IPE são fontes de pesquisa para fases posteriores. [DFP](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp) · [ITR](https://dados.cvm.gov.br/dataset/cia_aberta-doc-itr) · [IPE](https://dados.cvm.gov.br/dataset/cia_aberta-doc-ipe)

## Sprint 02

O painel contábil de 2019 a 2025 reúne a auditoria de duplicatas, o universo documental de emissores por exercício e nove indicadores candidatos. As tabelas usam a versão máxima identificada na captura e mantêm o escopo individual ou consolidado. O painel tem finalidade descritiva. A validação prospectiva depende da evidência de divulgação e das versões históricas dos valores. [Parecer e cobertura](docs/resultado-sprint-02.md) · [Inventário histórico](docs/historico-dfp.md) · [Auditoria de duplicatas](docs/auditoria-duplicatas.md) · [Dicionário dos indicadores](docs/conceitos-indicadores.md)

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

A integração contínua executa `uv run --locked pytest -m 'not dados_oficiais'` com fixtures locais. Para rodar somente a verificação com o arquivo oficial, configure a variável acima e use `uv run --locked pytest -m dados_oficiais`.

Execute todas as células do notebook e grave uma cópia com os resultados em `outputs/`.

```bash
uv run --locked jupyter nbconvert --to notebook --execute notebooks/01_exploracao_dfp.ipynb --output-dir outputs
```

O notebook localiza a captura processada de 2024. Quando houver mais de uma captura, defina a variável de ambiente `QUANTDISTRESS_DFP_SNAPSHOT` com o caminho para a pasta que contém o manifesto e os dois arquivos Parquet. Para exploração interativa, inicie `uv run --locked jupyter lab` na raiz e abra o notebook.

### Painel descritivo de 2019 a 2025

Execute na raiz do repositório. Estas instruções em PowerShell adquirem os arquivos atualmente publicados. Para reproduzir o recorte do relatório, preserve os ZIPs e as fontes cadastrais e confira seus hashes. [Inventário de capturas](docs/historico-dfp.md)

```powershell
$destinoCad = 'data/raw/cadastro/sprint02'
New-Item -ItemType Directory -Force $destinoCad | Out-Null
2019..2025 | ForEach-Object {
    uv run --locked quantdistress-dfp --ano $_
    if ($LASTEXITCODE -ne 0) { throw "Falha na ingestão DFP de $_" }
    curl.exe -fsSL "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_$_.zip" -o "$destinoCad/fca_cia_aberta_$_.zip"
    if ($LASTEXITCODE -ne 0) { throw "Falha no download FCA de $_" }
}
curl.exe -fsSL 'https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv' -o "$destinoCad/cad_cia_aberta.csv"
if ($LASTEXITCODE -ne 0) { throw 'Falha no download do cadastro CVM' }
uv run --locked python -m quantdistress.evaluation.panel --coleta-cadastral (Get-Date -Format 'yyyy-MM-dd')
uv run --locked jupyter nbconvert --to notebook --execute notebooks/02_painel_descritivo.ipynb --output-dir outputs
```

O painel aceita `--anos` para um subconjunto e `--snapshot ANO=SHA256` para resolver anos com mais de uma captura. A saída padrão é `data/processed/sprint02/`. Cada ano inclui o cadastro, fatos selecionados, indicadores com linhagem e a auditoria de duplicatas. Dois CSVs resumem cobertura por ano, escopo e setor. Se a saída já existir, informe um diretório novo com `--saida` e aponte `QUANTDISTRESS_PAINEL` para esse diretório ao executar o notebook.

## Estrutura e documentação

| Caminho | Conteúdo |
| --- | --- |
| `src/quantdistress/data/` | Aquisição, validação de estrutura, normalização e rastreabilidade da DFP |
| `src/quantdistress/evaluation/` | Diagnósticos de integridade e cobertura |
| `src/quantdistress/features/`, `src/quantdistress/scoring/` | Dicionário de contas, indicadores candidatos e espaço para futuros scores |
| `data/raw/`, `data/interim/`, `data/processed/` | Capturas brutas, tabelas de ingestão e painel analítico local |
| `notebooks/`, `tests/`, `outputs/` | Exploração, testes automatizados e resultados locais |

- [Metodologia de pesquisa](docs/metodologia.md)
- [Dicionário de dados da ingestão DFP](docs/dicionario-dados.md)
- [Cobertura e limitações da DFP 2024](docs/cobertura-dfp-2024.md)
- [Pendências da Sprint 02](docs/sprint-02.md)

O Git versiona código, configuração e documentação. Capturas brutas, Parquet, ambiente virtual e resultados gerados ficam nas pastas locais ignoradas. Fixtures sintéticas servem aos testes automatizados. O relatório de cobertura usa a captura oficial identificada por hash.
