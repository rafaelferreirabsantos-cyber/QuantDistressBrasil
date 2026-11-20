"""Gera o painel descritivo de contas e indicadores a partir de capturas locais verificadas."""

import argparse
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import BadZipFile

import pandas as pd

from quantdistress.data._snapshot import gravar_json, ler_json, sha256
from quantdistress.data.universe import (
    CHAVE_OBSERVACAO,
    CHAVE_REFERENCIA,
    construir_universo,
    ler_cadastro_atual,
    ler_fca,
)
from quantdistress.evaluation.duplicates import auditar_duplicatas
from quantdistress.features.indicators import calcular_indicadores

CHAVE_COBERTURA = ["ANO_ARQUIVO", "ESCOPO", "GRUPO_SETORIAL", "SETOR_FCA"]


def _abrir_snapshot(dados: Path, ano: int, hash_esperado: str | None):
    pasta = dados / "interim" / "dfp" / str(ano)
    candidatas = sorted(p.parent for p in pasta.glob("*/manifesto.json"))
    if hash_esperado:
        candidatas = [p for p in candidatas if p.name == hash_esperado]
    if len(candidatas) != 1:
        raise ValueError(f"Esperada uma captura para {ano}. Use --snapshot ANO=SHA256 se houver várias.")
    pasta = candidatas[0]
    manifesto = ler_json(pasta / "manifesto.json")
    if manifesto["ano"] != ano or manifesto["fonte"]["sha256"] != pasta.name:
        raise ValueError(f"Manifesto incompatível com {pasta}.")
    tabelas = []
    for nome in ("entregas", "fatos"):
        info = manifesto["tabelas"][nome]
        arquivo = pasta / f"{nome}.parquet"
        if sha256(arquivo) != info["sha256"]:
            raise ValueError(f"Hash divergente em {arquivo}.")
        tabela = pd.read_parquet(arquivo)
        if len(tabela) != info["linhas"]:
            raise ValueError(f"Contagem divergente em {arquivo}.")
        tabelas.append(tabela)
    return manifesto["fonte"], *tabelas


def _analisar_ano(dados, cadastro_atual, arquivo_fca, ano, hash_esperado, destino):
    fonte, entregas, fatos = _abrir_snapshot(dados, ano, hash_esperado)
    fca = ler_fca(arquivo_fca, ano)
    universo = construir_universo(entregas, fca, cadastro_atual).assign(
        ANO_ARQUIVO=ano,
        SHA256_DFP=fonte["sha256"],
        DT_COLETA_DFP=pd.Timestamp(fonte["capturado_em_utc"]),
    )
    referencias_invalidas = len(entregas[CHAVE_REFERENCIA].drop_duplicates()) - len(universo) // 2
    auditoria = auditar_duplicatas(fatos)
    selecao = auditoria.fatos_selecionados
    candidatas = universo.loc[universo["SITUACAO_ENTREGA_DFP"].eq("unica"), CHAVE_OBSERVACAO]
    selecao = selecao.loc[selecao["SITUACAO_VINCULO"].eq("unico")].merge(
        candidatas, on=CHAVE_OBSERVACAO, how="inner", validate="many_to_one",
    )
    contagem = (
        selecao.loc[selecao["ORDEM_EXERC"].eq("ÚLTIMO")]
        .groupby(CHAVE_OBSERVACAO).size().rename("N_FATOS_CORRENTES_SELECIONADOS").reset_index()
    )
    universo = universo.merge(contagem, on=CHAVE_OBSERVACAO, how="left", validate="one_to_one")
    universo["N_FATOS_CORRENTES_SELECIONADOS"] = universo["N_FATOS_CORRENTES_SELECIONADOS"].fillna(0).astype("Int64")
    indicadores = calcular_indicadores(selecao, universo, conflitos=auditoria.chaves_nao_resolvidas)

    # As partições anuais evitam concatenar milhões de fatos em memória.
    pasta = destino / str(ano)
    pasta.mkdir()
    universo.to_parquet(pasta / "universo.parquet", index=False)
    selecao.assign(ANO_ARQUIVO=ano, SHA256_DFP=fonte["sha256"]).to_parquet(
        pasta / "fatos_analiticos.parquet", index=False,
    )
    indicadores.to_parquet(pasta / "indicadores.parquet", index=False)
    for nome, tabela in (
        ("grupos_repetidos", auditoria.grupos_repetidos),
        ("linhas_repetidas", auditoria.linhas_repetidas),
    ):
        tabela.assign(ANO_ARQUIVO=ano, SHA256_DFP=fonte["sha256"]).to_parquet(
            pasta / f"{nome}.parquet", index=False,
        )

    resumo = universo.assign(
        COM_FATOS=universo["N_FATOS_CORRENTES_SELECIONADOS"].gt(0),
        FCA_IDENTIFICADO=universo["VINCULO_FCA"].eq("unico"),
        CANCELADA_DEPOIS=universo["CANCELAMENTO_POSTERIOR"].fillna(False),
    ).groupby(CHAVE_COBERTURA, dropna=False).agg(
        OBSERVACOES=("CD_CVM", "size"),
        EMISSORES=("CD_CVM", "nunique"),
        COM_FATOS=("COM_FATOS", "sum"),
        COM_FCA=("FCA_IDENTIFICADO", "sum"),
        COM_CANCELAMENTO_POSTERIOR=("CANCELADA_DEPOIS", "sum"),
    ).reset_index()
    cobertura = (
        indicadores.groupby([*CHAVE_COBERTURA, "EIXO", "INDICADOR", "SITUACAO"], dropna=False)
        .size().rename("OBSERVACOES").reset_index()
    )
    inventario = {
        "ano": ano,
        "fonte_dfp": fonte,
        "sha256_fca": sha256(arquivo_fca),
        "url_fca": f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/{arquivo_fca.name}",
        "linhas_fca": len(fca),
        "registros_indice_dfp": len(entregas),
        "referencias_indice_excluidas_por_chave_invalida": referencias_invalidas,
        "observacoes_universo": len(universo),
        "fatos_na_fonte": len(fatos),
        "fatos_analiticos": len(selecao),
        "observacoes_indicadores": len(indicadores),
        "chaves_contabeis_nao_resolvidas": len(auditoria.chaves_nao_resolvidas),
    }
    return resumo, cobertura, inventario


def gerar_painel(
    dados: Path, cadastros: Path, anos, destino: Path, snapshots=None, *, coleta_cadastral: date | None = None,
) -> Path:
    """Publica a execução em uma pasta nova, somente após finalizar todos os anos."""
    destino = destino.resolve()
    if destino.exists():
        raise ValueError(f"A saída já existe. Escolha um novo diretório: {destino}.")
    anos = sorted(set(anos))
    if not anos:
        raise ValueError("Informe ao menos um ano para o painel.")
    snapshots = snapshots or {}
    arquivo_cad = cadastros / "cad_cia_aberta.csv"
    cadastro = ler_cadastro_atual(arquivo_cad)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".painel-", dir=destino.parent) as pasta:
        temporario = Path(pasta)
        dados_anuais = [
            _analisar_ano(dados, cadastro, cadastros / f"fca_cia_aberta_{ano}.zip", ano, snapshots.get(ano), temporario)
            for ano in anos
        ]
        setores, indicadores, inventario = zip(*dados_anuais)
        pd.concat(setores, ignore_index=True).to_csv(temporario / "cobertura_setor.csv", index=False)
        pd.concat(indicadores, ignore_index=True).to_csv(temporario / "cobertura_indicadores.csv", index=False)
        gravar_json(temporario / "manifesto.json", {
            "modo_temporal": "descritivo_revisado",
            "protocolo": 1,
            "data_coleta_fca_e_cad_informada": coleta_cadastral.isoformat() if coleta_cadastral else None,
            "sha256_cad_coleta": sha256(arquivo_cad),
            "url_cad_coleta": "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv",
            "anos": list(inventario),
        })
        # A renomeação falha caso outra execução já tenha publicado o destino.
        temporario.rename(destino)
    return destino


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera o painel contábil histórico descritivo.")
    parser.add_argument("--dados", type=Path, default=Path("data"))
    parser.add_argument("--cadastros", type=Path, default=Path("data/raw/cadastro/sprint02"))
    parser.add_argument("--anos", type=int, nargs="+", default=list(range(2019, 2026)))
    parser.add_argument("--saida", type=Path, default=Path("data/processed/sprint02"))
    parser.add_argument("--snapshot", action="append", metavar="ANO=SHA256", default=[])
    parser.add_argument("--coleta-cadastral", type=date.fromisoformat, help="Data declarada da captura FCA/CAD (AAAA-MM-DD).")
    args = parser.parse_args()
    try:
        snapshots = {int(ano): digest for ano, digest in (item.split("=", 1) for item in args.snapshot)}
        resultado = gerar_painel(
            args.dados, args.cadastros, args.anos, args.saida, snapshots, coleta_cadastral=args.coleta_cadastral,
        )
    except (ValueError, OSError, KeyError, BadZipFile) as erro:
        parser.exit(1, f"Falha na geração do painel: {erro}\n")
    print(resultado)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
