"""Diagnósticos descritivos para snapshots de DFP."""

from decimal import Decimal, localcontext

import pandas as pd

from quantdistress.data.dfp import CHAVE_ENTREGA as CHAVE_ENTREGA_DFP


CHAVE_ENTREGA = list(CHAVE_ENTREGA_DFP)
CHAVE_PERIODO = [
    *CHAVE_ENTREGA, "ESCOPO", "ORDEM_EXERC", "DT_INI_EXERC", "DT_FIM_EXERC",
]
CONTAS_CANDIDATAS = {
    "BPA": ("1", "1.01"),
    "BPP": ("2", "2.01", "2.03"),
    "DRE": ("3.01", "3.05", "3.11"),
    "DFC_MD": ("6.01",),
    "DFC_MI": ("6.01",),
}


def cobertura_por_demonstracao(fatos: pd.DataFrame) -> pd.DataFrame:
    """Conta linhas, emissores, chaves de entrega e ordens de exercício."""
    cobertura = fatos.groupby(["ESCOPO", "FAMILIA"]).agg(
        LINHAS=("CD_CONTA", "size"),
        EMISSORES=("CD_CVM", "nunique"),
    )
    chaves = fatos[["ESCOPO", "FAMILIA", *CHAVE_ENTREGA]].drop_duplicates()
    cobertura["CHAVES_ENTREGA"] = chaves.groupby(["ESCOPO", "FAMILIA"]).size()
    ordens = (
        fatos.groupby(["ESCOPO", "FAMILIA", "ORDEM_EXERC"], dropna=False)
        .size()
        .unstack(fill_value=0)
    )
    return cobertura.join(ordens)


def cobertura_por_escopo(fatos: pd.DataFrame, entregas: pd.DataFrame) -> pd.DataFrame:
    """Conta presença de blocos contábeis no último exercício por chave de entrega."""
    ultimo = fatos.loc[
        fatos["ORDEM_EXERC"].eq("ÚLTIMO"), [*CHAVE_ENTREGA, "ESCOPO", "FAMILIA"]
    ].drop_duplicates()
    cobertura = pd.crosstab(
        [ultimo[c] for c in (*CHAVE_ENTREGA, "ESCOPO")], ultimo["FAMILIA"]
    ).reindex(columns=list(CONTAS_CANDIDATAS), fill_value=0).astype(bool)
    cobertura["ALGUMA_DFC"] = cobertura["DFC_MD"] | cobertura["DFC_MI"]
    cobertura["AMBOS_METODOS_DFC"] = cobertura["DFC_MD"] & cobertura["DFC_MI"]
    cobertura["BPA_BPP_DRE_DFC"] = cobertura[["BPA", "BPP", "DRE", "ALGUMA_DFC"]].all(axis=1)

    indice = pd.MultiIndex.from_frame(entregas[CHAVE_ENTREGA].drop_duplicates())
    no_indice = cobertura.index.droplevel("ESCOPO").isin(indice)
    cobertura_indice = cobertura.loc[no_indice]
    escopos = fatos["ESCOPO"].drop_duplicates().sort_values().rename("ESCOPO")
    resumo = cobertura_indice.groupby(level="ESCOPO").sum().reindex(escopos, fill_value=0)
    resumo["COM_ALGUMA_DEMONSTRACAO"] = (
        cobertura_indice.groupby(level="ESCOPO").size().reindex(escopos, fill_value=0)
    )
    resumo["COM_DEMONSTRACAO_FORA_DO_INDICE"] = (
        cobertura.loc[~no_indice].groupby(level="ESCOPO").size().reindex(escopos, fill_value=0)
    )
    resumo["TOTAL_CHAVES_NO_INDICE"] = len(indice)
    resumo["SEM_DEMONSTRACAO_NO_ESCOPO"] = (
        resumo["TOTAL_CHAVES_NO_INDICE"] - resumo["COM_ALGUMA_DEMONSTRACAO"]
    )
    return resumo.rename_axis(columns="MEDIDA")


def integridade_por_demonstracao(fatos: pd.DataFrame) -> pd.DataFrame:
    """Conta linhas afetadas por chave repetida, repetição exata, vínculo ou nulos."""
    indicador = fatos[["ESCOPO", "FAMILIA", "CHAVE_REPETIDA", "FATO_REPETIDO"]].copy()
    indicador["VINCULO_AMBIGUO"] = fatos["SITUACAO_VINCULO"].eq("ambiguo")
    indicador["VINCULO_AUSENTE"] = fatos["SITUACAO_VINCULO"].eq("ausente")
    indicador["VALOR_AUSENTE"] = fatos["VL_CONTA"].isna() | fatos["VL_CONTA"].eq("")
    indicador["ESCALA_DESCONHECIDA"] = fatos["FATOR_ESCALA_MOEDA"].isna()
    return indicador.groupby(["ESCOPO", "FAMILIA"]).sum()


def rotulos_contas_candidatas(fatos: pd.DataFrame) -> pd.DataFrame:
    """Mostra rótulos e cobertura bruta de contas candidatas antes de padronização."""
    ultimo = fatos.loc[fatos["ORDEM_EXERC"].eq("ÚLTIMO")]
    contas = [
        (familia, conta) for familia, codigos in CONTAS_CANDIDATAS.items() for conta in codigos
    ]
    amostra = ultimo.loc[
        pd.MultiIndex.from_frame(ultimo[["FAMILIA", "CD_CONTA"]]).isin(contas),
        [*CHAVE_ENTREGA, "ESCOPO", "FAMILIA", "CD_CONTA", "DS_CONTA"],
    ].drop_duplicates()
    return (
        amostra.groupby(["ESCOPO", "FAMILIA", "CD_CONTA", "DS_CONTA"], dropna=False)
        .size()
        .rename("CHAVES_ENTREGA")
        .reset_index()
    )


def conciliacao_patrimonial(fatos: pd.DataFrame) -> pd.DataFrame:
    """Compara os totais BPA 1 e BPP 2 com tolerância de uma unidade da maior escala."""
    ativo = fatos["FAMILIA"].eq("BPA") & fatos["CD_CONTA"].eq("1")
    passivo = fatos["FAMILIA"].eq("BPP") & fatos["CD_CONTA"].eq("2")
    colunas = [*CHAVE_PERIODO, "MOEDA", "VL_CONTA", "FATOR_ESCALA_MOEDA"]
    totais = fatos.loc[ativo | passivo, [*colunas, "FAMILIA"]].drop_duplicates()
    totais["MULTIPLOS_TOTAIS"] = totais.duplicated([*CHAVE_PERIODO, "FAMILIA"], keep=False)
    totais = totais.drop_duplicates([*CHAVE_PERIODO, "FAMILIA"])

    pares = totais.loc[totais["FAMILIA"].eq("BPA")].merge(
        totais.loc[totais["FAMILIA"].eq("BPP")],
        on=CHAVE_PERIODO,
        how="outer",
        suffixes=("_BPA", "_BPP"),
        indicator=True,
    )
    ambiguos = (
        pares["MULTIPLOS_TOTAIS_BPA"].notna() & pares["MULTIPLOS_TOTAIS_BPA"].eq(True)
    ) | (
        pares["MULTIPLOS_TOTAIS_BPP"].notna() & pares["MULTIPLOS_TOTAIS_BPP"].eq(True)
    )
    validos = (
        pares["_merge"].eq("both")
        & pares["MOEDA_BPA"].notna()
        & pares["MOEDA_BPA"].eq(pares["MOEDA_BPP"])
        & pares["VL_CONTA_BPA"].notna()
        & pares["VL_CONTA_BPP"].notna()
        & pares["VL_CONTA_BPA"].ne("")
        & pares["VL_CONTA_BPP"].ne("")
        & pares["FATOR_ESCALA_MOEDA_BPA"].notna()
        & pares["FATOR_ESCALA_MOEDA_BPP"].notna()
        & ~ambiguos
    )

    pares["SITUACAO"] = "moeda_escala_ou_valor_invalido"
    pares.loc[pares["_merge"].ne("both"), "SITUACAO"] = "sem_par"
    pares.loc[ambiguos, "SITUACAO"] = "multiplos_totais"
    pares["DIFERENCA_EM_UNIDADES"] = pd.Series(None, index=pares.index, dtype="object")
    pares["TOLERANCIA_EM_UNIDADES"] = pd.Series(None, index=pares.index, dtype="object")
    with localcontext() as contexto:
        contexto.prec = 38
        for par in pares.loc[validos].itertuples():
            escala_a = int(par.FATOR_ESCALA_MOEDA_BPA)
            escala_p = int(par.FATOR_ESCALA_MOEDA_BPP)
            diferenca = Decimal(par.VL_CONTA_BPA) * escala_a - Decimal(par.VL_CONTA_BPP) * escala_p
            tolerancia = max(escala_a, escala_p)
            pares.at[par.Index, "DIFERENCA_EM_UNIDADES"] = diferenca
            pares.at[par.Index, "TOLERANCIA_EM_UNIDADES"] = tolerancia
            pares.at[par.Index, "SITUACAO"] = (
                "dentro_da_tolerancia" if abs(diferenca) <= tolerancia else "acima_da_tolerancia"
            )
    return pares[[*CHAVE_PERIODO, "SITUACAO", "DIFERENCA_EM_UNIDADES", "TOLERANCIA_EM_UNIDADES"]]
