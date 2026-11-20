import numpy as np
import pandas as pd
import pytest

from quantdistress.evaluation.references03 import AmostraReferencia, agrupar_referencias, percentil_ponto_medio


@pytest.mark.parametrize("minimo", [15, 30, 50])
def test_limiar_conta_pares_depois_de_excluir_codigo(minimo):
    ref = pd.Series(np.arange(minimo, dtype=float), index=[str(i) for i in range(minimo)])
    amostra = AmostraReferencia(ref)
    assert amostra.preparar(min_pares=minimo).situacao == "utilizavel"
    excluido = amostra.preparar(min_pares=minimo, emissor_excluido="0")
    assert (excluido.n_pares, excluido.situacao) == (minimo - 1, "insuficiente")
    ref.loc["novo"] = 0
    exato = AmostraReferencia(ref).preparar(min_pares=minimo, emissor_excluido="0")
    assert (exato.n_pares, exato.situacao) == (minimo, "utilizavel")


def test_empates_ausentes_e_distribuicao_constante_na_referencia_excluida():
    ref = pd.Series([0, 0, 2, np.nan, np.inf], index=["1", "2", "3", "4", "5"])
    amostra = AmostraReferencia(ref)
    inclusiva = amostra.preparar(min_pares=2)
    assert inclusiva.n_pares == 3 and inclusiva.maior_empate == 2
    assert percentil_ponto_medio(0, inclusiva) == pytest.approx(100 / 3)
    sem_um_zero = amostra.preparar(min_pares=2, emissor_excluido="1")
    assert percentil_ponto_medio(0, sem_um_zero) == 25
    assert np.isnan(percentil_ponto_medio(np.nan, sem_um_zero))
    constante = amostra.preparar(min_pares=2, emissor_excluido="3")
    assert (constante.n_pares, constante.situacao) == (2, "constante")
    assert np.isnan(percentil_ponto_medio(2, constante))


def test_coorte_isola_setor_ano_escopo_e_rejeita_emissor_duplicado():
    colunas = ["ANO_ARQUIVO", "ESCOPO", "SETOR_FCA", "CD_CVM", "VALOR"]
    base = pd.DataFrame([
        [2024, "con", "A", "1", 1.0], [2024, "con", "A", "2", 2.0],
        [2024, "con", "B", "2", 9.0], [2024, "ind", "A", "2", 10.0],
        [2023, "con", "A", "1", 30.0], [2023, "con", "A", "2", 40.0],
    ], columns=colunas)
    grupos = agrupar_referencias(base, colunas[:3])
    assert grupos[(2024, "con", "A")].tolist() == [1, 2]
    anterior = AmostraReferencia(grupos[(2023, "con", "A")]).preparar(min_pares=2, emissor_excluido="1")
    assert anterior.valores.tolist() == [40]
    with pytest.raises(ValueError, match="mesmo emissor"):
        agrupar_referencias(pd.concat([base, base.iloc[:1]]), colunas[:3])
