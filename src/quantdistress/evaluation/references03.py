"""Identidade, seleção de referência e percentil para diagnósticos descritivos."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


def selecionar_ultima_referencia(tabela: pd.DataFrame, *, por_indicador: bool = False) -> pd.Series:
    """Escolhe a última referência por emissor, ano e escopo antes de testar o valor."""
    chaves = ["ANO_ARQUIVO", "CD_CVM", "ESCOPO"]
    if por_indicador:
        chaves.append("INDICADOR")
    grupos = [tabela[coluna] for coluna in chaves]
    ultimo = tabela["DT_REFER"].groupby(grupos).transform("max")
    candidatas = tabela["DT_REFER"].eq(ultimo)
    return candidatas & candidatas.groupby(grupos).transform("sum").eq(1)


def agrupar_referencias(tabela: pd.DataFrame, chaves: list[str]) -> dict[tuple, pd.Series]:
    """Separa referências por coorte e assegura no máximo uma linha por código CVM."""
    if tabela.duplicated([*chaves, "CD_CVM"]).any():
        raise ValueError("Mais de uma referência para o mesmo emissor na coorte.")
    valores = tabela["VALOR"].to_numpy(dtype=float, na_value=np.nan)
    finitos = tabela.loc[np.isfinite(valores) & tabela["CD_CVM"].notna()]
    return {chave: grupo.set_index("CD_CVM")["VALOR"] for chave, grupo in finitos.groupby(chaves)}


@dataclass(frozen=True)
class Referencia:
    valores: np.ndarray
    n_pares: int
    situacao: str
    maior_empate: int


class AmostraReferencia:
    """Indexa valores finitos uma vez para avaliar diversos alvos da coorte."""

    def __init__(self, serie: pd.Series):
        if not serie.index.is_unique:
            raise ValueError("A referência exige uma linha por código CVM.")
        valores = serie.to_numpy(dtype=float, na_value=np.nan)
        finitos = np.isfinite(valores) & serie.index.notna()
        self._valores = valores[finitos]
        self._posicoes = {codigo: pos for pos, codigo in enumerate(serie.index[finitos])}

    def preparar(self, *, min_pares: int, emissor_excluido: str | None = None) -> Referencia:
        """Conta emissores após excluir o código do alvo, inclusive em outro ano."""
        if min_pares < 2:
            raise ValueError("São necessários pelo menos dois pares.")
        posicao = self._posicoes.get(emissor_excluido)
        vetor = self._valores if posicao is None else np.delete(self._valores, posicao)
        n = len(vetor)
        distintos, frequencias = np.unique(vetor, return_counts=True)
        if n < min_pares:
            situacao = "insuficiente"
        elif len(distintos) < 2:
            situacao = "constante"
        else:
            situacao = "utilizavel"
        return Referencia(vetor, n, situacao, int(frequencias.max()) if n else 0)


def percentil_ponto_medio(alvo: float, referencia: Referencia) -> float:
    """Calcula posição relativa de um componente para comparações agregadas."""
    if referencia.situacao != "utilizavel" or pd.isna(alvo) or not np.isfinite(alvo):
        return np.nan
    anteriores = np.count_nonzero(referencia.valores < alvo)
    iguais = np.count_nonzero(referencia.valores == alvo)
    return 100 * (anteriores + iguais / 2) / referencia.n_pares
