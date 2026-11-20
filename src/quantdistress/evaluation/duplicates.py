"""Auditoria de chaves contábeis repetidas em uma captura DFP."""

from dataclasses import dataclass
from decimal import Decimal

import numpy as np
import pandas as pd

from quantdistress.data.dfp import CHAVE_FATO, COLUNAS_FATO, METADADOS_DOCUMENTO

CHAVE_CONTABIL = (*CHAVE_FATO, "FAMILIA", "ESCOPO")
_CHAVE_OBRIGATORIA = tuple(campo for campo in CHAVE_CONTABIL if campo != "DT_INI_EXERC")
_ORIGEM = ("ARQUIVO_ORIGEM", "LINHA_ORIGEM")
_CAMPOS_COMPARAVEIS = tuple(campo for campo in COLUNAS_FATO if campo not in CHAVE_CONTABIL)
_METADADOS_COMPARAVEIS = (*METADADOS_DOCUMENTO, "SITUACAO_VINCULO", "FATOR_ESCALA_MOEDA")


@dataclass(frozen=True)
class AuditoriaDuplicatas:
    """Seleção derivada e trilha de auditoria das repetições da captura."""

    fatos_selecionados: pd.DataFrame
    grupos_repetidos: pd.DataFrame
    linhas_repetidas: pd.DataFrame

    @property
    def chaves_nao_resolvidas(self) -> pd.DataFrame:
        """Retorna as chaves que exigem revisão antes da seleção analítica."""
        return self.grupos_repetidos.loc[~self.grupos_repetidos["RESOLVIDA"]].copy()


def _diverge_em_valor(valores: pd.Series) -> bool:
    distintos = valores.unique()
    if len(distintos) <= 1:
        return False
    return len({None if pd.isna(valor) else Decimal(valor) for valor in distintos}) > 1


def auditar_duplicatas(fatos: pd.DataFrame) -> AuditoriaDuplicatas:
    """Preserva chaves únicas e escolhe uma origem só para repetições completas idênticas.

    Recebe os fatos de uma única captura. Retém os registros originais de todos os
    grupos, inclusive das chaves removidas da seleção, sem modificar o DataFrame
    recebido. A seleção resolve repetição e deve passar pelas demais regras analíticas.
    """
    chave = list(CHAVE_CONTABIL)
    comparaveis = [*_CAMPOS_COMPARAVEIS, *(c for c in _METADADOS_COMPARAVEIS if c in fatos)]
    faltantes = sorted({*chave, *_ORIGEM, *comparaveis} - set(fatos.columns))
    if faltantes:
        raise ValueError(f"Campos necessários para auditar duplicatas: {', '.join(faltantes)}.")
    if fatos[list(_ORIGEM)].isna().any(axis=None) or fatos.duplicated(list(_ORIGEM)).any():
        raise ValueError("A linhagem física dos fatos deve ser única e preenchida na captura.")

    mascara_repetidas = fatos.duplicated(chave, keep=False).to_numpy()
    repetidas = fatos.loc[mascara_repetidas].sort_values(list(_ORIGEM))
    agrupadas = repetidas.groupby(chave, dropna=False, sort=False, observed=True)
    variacoes = agrupadas[comparaveis].nunique(dropna=False).gt(1)
    if "FATO_REPETIDO" in repetidas:
        confirmadas_na_fonte = agrupadas["FATO_REPETIDO"].all(skipna=False).fillna(False)
        variacoes["FATO_REPETIDO"] = ~variacoes.any(axis=1) & ~confirmadas_na_fonte
    dif_valor = agrupadas["VL_CONTA"].agg(_diverge_em_valor).astype(bool)
    dif_rotulo = variacoes["DS_CONTA"]
    dif_outros = (
        variacoes.drop(columns=["VL_CONTA", "DS_CONTA"]).any(axis=1)
        | (variacoes["VL_CONTA"] & ~dif_valor)
    )
    tipo_contagem = dif_valor.astype(int) + dif_rotulo.astype(int) + dif_outros.astype(int)

    grupos = agrupadas.size().rename("N_LINHAS").reset_index()
    grupos["CLASSE_DUPLICATA"] = pd.array(
        np.select(
            [tipo_contagem.eq(0), tipo_contagem.gt(1), dif_valor, dif_rotulo],
            ["exata", "mista", "valor", "rotulo"],
            default="outros",
        ),
        dtype="string",
    )
    grupos["DIFERENCA_VALOR"] = dif_valor.to_numpy()
    grupos["DIFERENCA_ROTULO"] = dif_rotulo.to_numpy()
    grupos["DIFERENCA_OUTROS"] = dif_outros.to_numpy()
    grupos["CAMPOS_DIVERGENTES"] = pd.array(
        [
            ",".join(campo for campo, difere in zip(variacoes.columns, variacao, strict=True) if difere)
            for variacao in variacoes.itertuples(index=False, name=None)
        ],
        dtype="string",
    )
    grupos["CHAVE_COMPLETA"] = grupos[list(_CHAVE_OBRIGATORIA)].notna().all(axis=1) & (
        grupos["DT_INI_EXERC"].notna() | grupos["FAMILIA"].isin(["BPA", "BPP"])
    )
    grupos["RESOLVIDA"] = grupos["CLASSE_DUPLICATA"].eq("exata") & grupos["CHAVE_COMPLETA"]

    primeiras = agrupadas[list(_ORIGEM)].first().reset_index(drop=True)
    grupos["ARQUIVO_SELECIONADO"] = primeiras["ARQUIVO_ORIGEM"].where(grupos["RESOLVIDA"]).astype("string")
    grupos["LINHA_SELECIONADA"] = primeiras["LINHA_ORIGEM"].where(grupos["RESOLVIDA"]).astype("Int64")

    linhas = repetidas.merge(grupos, on=chave, how="left", validate="many_to_one")
    linhas["SELECIONADA_ANALITICA"] = linhas["RESOLVIDA"] & linhas["ARQUIVO_ORIGEM"].eq(
        linhas["ARQUIVO_SELECIONADO"]
    ) & linhas["LINHA_ORIGEM"].eq(linhas["LINHA_SELECIONADA"])
    origens_escolhidas = pd.MultiIndex.from_frame(
        linhas.loc[linhas["SELECIONADA_ANALITICA"], list(_ORIGEM)]
    )
    origens_repetidas = pd.MultiIndex.from_frame(fatos.loc[mascara_repetidas, list(_ORIGEM)])
    mascara_selecao = ~mascara_repetidas
    mascara_selecao[mascara_repetidas] = origens_repetidas.isin(origens_escolhidas)
    return AuditoriaDuplicatas(fatos.loc[mascara_selecao].copy(), grupos, linhas)
