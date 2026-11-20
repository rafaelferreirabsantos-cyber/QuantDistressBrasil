"""Gera os scores experimentais e a matriz descritiva com saídas locais auditáveis."""

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from quantdistress.data._snapshot import gravar_json, ler_json, sha256
from quantdistress.evaluation.matrix03b import contar_matriz, renderizar_matriz
from quantdistress.evaluation.sensitivity03b import MODO, analisar_sensibilidade, cenarios_sensibilidade

from .experimental import Scenario, calculate_scores, load_panel


def _fingerprint(painel: Path, dados: Path) -> tuple[str, dict]:
    arquivo = painel / "manifesto.json"
    manifesto = ler_json(arquivo)
    particoes = {}
    for item in manifesto["anos"]:
        ano, digest = str(item["ano"]), item["fonte_dfp"]["sha256"]
        origem = dados / "interim" / "dfp" / ano / digest
        particoes[ano] = {
            "sha256_indicadores": sha256(painel / ano / "indicadores.parquet"),
            "sha256_zip_dfp": digest,
            "intermediarios_dfp": {
                nome: sha256(origem / nome) if (origem / nome).is_file() else None
                for nome in ("manifesto.json", "fatos.parquet")
            },
        }
    return sha256(arquivo), particoes


def executar(painel: Path, dados: Path, saida: Path) -> Path:
    """Publica os arquivos em um diretório novo após concluir as verificações."""
    saida = saida.resolve()
    if saida.exists():
        raise FileExistsError(f"A saída já existe. Escolha outro diretório: {saida}")
    entrada = _fingerprint(painel, dados)
    fonte = load_panel(painel, dados)
    benchmark = Scenario(name="benchmark_exato")
    scores, componentes = calculate_scores(fonte, benchmark)
    alternativas = {}
    configuracoes = [{"config_id": benchmark.config_id, **benchmark.metadata()}]
    saida.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".sprint03b-", dir=saida.parent) as nome:
        pasta = Path(nome)
        scores.to_parquet(pasta / "scores.parquet", index=False)
        componentes.to_parquet(pasta / "componentes.parquet", index=False)
        for cenario in cenarios_sensibilidade(benchmark):
            painel_alt, componentes_alt = calculate_scores(fonte, cenario)
            alternativas[cenario.name] = painel_alt
            configuracoes.append({"config_id": cenario.config_id, **cenario.metadata()})
            if cenario.macro:
                painel_alt.to_parquet(pasta / "scores_macrosetores.parquet", index=False)
                componentes_alt.to_parquet(pasta / "componentes_macrosetores.parquet", index=False)
        tabelas = analisar_sensibilidade(scores, alternativas, benchmark.name)
        matriz = contar_matriz(scores)
        tabelas["matriz_faixas"] = matriz
        anos = scores["ANO_ARQUIVO"]
        renderizar_matriz(matriz, pasta / "matriz_quality_distress.png", (int(anos.min()), int(anos.max())))
        for nome_tabela, tabela in tabelas.items():
            tabela.assign(MODO_TEMPORAL=MODO).to_csv(pasta / f"{nome_tabela}.csv", index=False)
        gravar_json(pasta / "configuracoes.json", {"modo_temporal": MODO, "cenarios": configuracoes})
        if entrada != _fingerprint(painel, dados):
            raise ValueError("As partições de entrada foram alteradas durante a execução.")
        gravar_json(pasta / "manifesto.json", {
            "modo_temporal": MODO,
            "sha256_manifesto_painel": entrada[0],
            "particoes": entrada[1],
            "observacoes_benchmark": len(scores),
            "componentes_benchmark": len(componentes),
            "linhas_tabelas": {nome: len(tabela) for nome, tabela in tabelas.items()},
            "sha256_saidas": {arquivo.name: sha256(arquivo) for arquivo in sorted(pasta.iterdir())},
        })
        pasta.rename(saida)
    return saida


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--painel", type=Path, default=Path("data/processed/sprint02"))
    parser.add_argument("--dados", type=Path, default=Path("data"))
    parser.add_argument("--saida", type=Path, default=Path("outputs/sprint03b"))
    args = parser.parse_args()
    try:
        destino = executar(args.painel, args.dados, args.saida)
    except (OSError, ValueError, KeyError) as erro:
        parser.exit(1, f"Falha ao gerar o painel da Sprint 03B: {erro}\n")
    print(destino)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
