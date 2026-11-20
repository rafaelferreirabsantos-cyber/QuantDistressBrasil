"""Inventário descritivo de versões no índice e nos fatos das capturas DFP."""

import argparse
import json
from pathlib import Path

import pandas as pd

from ._snapshot import ler_json, sha256
from .dfp import CHAVE_ENTREGA


def resumir_versoes(entregas: pd.DataFrame, fatos: pd.DataFrame) -> dict:
    """Compara chaves completas, mantendo separadas a versão e a sua disponibilidade."""
    chave = list(CHAVE_ENTREGA)
    chave_periodo = [campo for campo in chave if campo != "VERSAO"]
    registros = entregas[chave].dropna()
    indice = registros.drop_duplicates()
    chaves_fatos = fatos[chave].dropna().drop_duplicates()
    versoes_por_periodo = indice.groupby(chave_periodo)["VERSAO"]
    maximas = versoes_por_periodo.max().rename("VERSAO_MAXIMA")

    cobertura_indice = indice.merge(chaves_fatos, how="left", on=chave, indicator=True)
    comparacao = cobertura_indice.merge(maximas, on=chave_periodo, validate="many_to_one")
    com_fatos = comparacao["_merge"].eq("both")
    maior_versao = comparacao["VERSAO"].eq(comparacao["VERSAO_MAXIMA"])
    data_recebimento = entregas["DT_RECEB"].dropna()

    return {
        "chaves_indice": len(indice),
        "linhas_indice_chave_incompleta": len(entregas) - len(registros),
        "periodos_indice_com_multiplas_versoes": int(versoes_por_periodo.size().gt(1).sum()),
        "linhas_por_versao_indice": {
            str(versao): int(total) for versao, total in registros["VERSAO"].value_counts().sort_index().items()
        },
        "chaves_fatos": len(chaves_fatos),
        "linhas_fatos_chave_incompleta": int(fatos[chave].isna().any(axis=1).sum()),
        "chaves_fatos_sem_indice": len(chaves_fatos) - int(com_fatos.sum()),
        "chaves_maximas_com_fatos": int((maior_versao & com_fatos).sum()),
        "chaves_maximas_sem_fatos": int((maior_versao & ~com_fatos).sum()),
        "chaves_anteriores_com_fatos": int((~maior_versao & com_fatos).sum()),
        "chaves_anteriores_sem_fatos": int((~maior_versao & ~com_fatos).sum()),
        "primeiro_recebimento": None if data_recebimento.empty else data_recebimento.min().date().isoformat(),
        "ultimo_recebimento": None if data_recebimento.empty else data_recebimento.max().date().isoformat(),
    }


def inventariar_captura(pasta: Path) -> dict:
    """Confere a integridade da captura antes de medir presença das versões."""
    manifesto = ler_json(pasta / "manifesto.json")
    tabelas = manifesto["tabelas"]
    quadros = {}
    for nome, colunas in (
        ("entregas", [*CHAVE_ENTREGA, "DT_RECEB"]),
        ("fatos", list(CHAVE_ENTREGA)),
    ):
        caminho = pasta / f"{nome}.parquet"
        if sha256(caminho) != tabelas[nome]["sha256"]:
            raise ValueError(f"Parquet diverge do manifesto: {caminho}")
        quadro = pd.read_parquet(caminho, columns=colunas)
        if len(quadro) != tabelas[nome]["linhas"]:
            raise ValueError(f"Contagem de registros diverge do manifesto: {caminho}")
        quadros[nome] = quadro

    ajustes_csv = [
        {"arquivo": membro["arquivo"], **membro["ajustes_csv"]}
        for membro in manifesto["membros_processados"]
        if "ajustes_csv" in membro
    ]
    return {
        "ano": manifesto["ano"],
        "fonte": manifesto["fonte"],
        "linhas_entregas": len(quadros["entregas"]),
        "linhas_fatos": len(quadros["fatos"]),
        "membros_processados": len(manifesto["membros_processados"]),
        "membros_inventariados": len(manifesto["membros_fora_escopo"]),
        "ajustes_csv": ajustes_csv,
        **resumir_versoes(quadros["entregas"], quadros["fatos"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventaria versões em capturas DFP já processadas.")
    parser.add_argument("capturas", type=Path, nargs="+", help="Pastas que contêm os manifestos.")
    argumentos = parser.parse_args()
    inventario = [inventariar_captura(pasta) for pasta in argumentos.capturas]
    print(json.dumps(inventario, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
