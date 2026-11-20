import numpy as np
import pandas as pd
import pytest

from quantdistress.evaluation.normalization03 import (
    _normalizar,
    _perturbar_cauda,
    experimentar_normalizacao,
)


def test_percentil_usa_meia_massa_dos_empates_e_preserva_ausentes():
    alvos = np.array([-1, 0, 1, 3, 4, np.inf, np.nan])
    ref = np.array([0, 0, 2, 3, np.nan])
    pontos = _normalizar(alvos, ref, "percentil", 4)
    np.testing.assert_allclose(pontos, [0, 25, 50, 87.5, 100, np.nan, np.nan])
    assert np.isnan(_normalizar(alvos, ref, "percentil", 5)).all()
    assert np.isnan(_normalizar(alvos, np.array([0, 0, 0]), "percentil", 3)).all()


def test_robusto_usa_iqr_quando_mad_zero_e_abstem_quando_iqr_zero():
    alvos = np.array([0.0, 1.0])
    mediana_zero = np.array([0, 0, 0, 0, 1, 2], dtype=float)
    assert _normalizar(alvos, mediana_zero, "robusto", 2)[0] == 50
    assert _normalizar(alvos, mediana_zero, "robusto", 2)[1] > 50
    mediana_e_iqr_zero = np.array([0] * 9 + [1], dtype=float)
    assert np.isnan(_normalizar(alvos, mediana_e_iqr_zero, "robusto", 2)).all()


def test_perturbacao_so_troca_maximo_da_referencia_e_percentil_limita_movimento():
    ref = np.array([1., 2., 3., 4., 5.])
    x = np.array([2., 4.])
    perturbada = _perturbar_cauda(ref)
    np.testing.assert_array_equal(ref, [1., 2., 3., 4., 5.])
    np.testing.assert_array_equal(perturbada, [1., 2., 3., 4., 405.])
    np.testing.assert_allclose(
        _normalizar(x, ref, "percentil", 2), _normalizar(x, perturbada, "percentil", 2),
    )
    assert not np.allclose(_normalizar(x, ref, "z", 2), _normalizar(x, perturbada, "z", 2))


def _observacao(ano, emissor, valor, *, escopo="con", mes=12, setor="A", situacao="valido"):
    return {
        "ANO_ARQUIVO": ano, "DT_REFER": pd.Timestamp(ano, mes, 28), "CD_CVM": emissor,
        "ESCOPO": escopo, "SETOR_FCA": setor, "GRUPO_SETORIAL": "nao_financeira",
        "INDICADOR": "margem_operacional", "SITUACAO": situacao, "VALOR": valor,
    }


def test_experimento_separa_escopos_e_usa_apenas_referencia_anterior_sem_reaproveitar_dado_antigo():
    painel = pd.DataFrame([
        _observacao(2019, "1", 1000.0), _observacao(2019, "2", 1001.0),
        _observacao(2020, "1", 1.0), _observacao(2020, "2", 3.0),
        _observacao(2020, "3", 2.0, mes=6), _observacao(2020, "3", np.nan, situacao="conta_ausente"),
        _observacao(2020, "4", 3.0), _observacao(2020, "4", 4.0),  # Mesma data e sem identificação única.
        _observacao(2020, "5", 2.0, escopo="ind"), _observacao(2020, "6", 3.0, escopo="ind"),
        _observacao(2021, "1", 2.0), _observacao(2021, "2", 3.0), _observacao(2021, "3", 4.0, setor="B"),
        _observacao(2022, "1", 200.0), _observacao(2022, "2", 201.0),
    ])
    resultado = experimentar_normalizacao(painel, min_pares=2).set_index(["ANO_ARQUIVO", "ESCOPO", "METODO"])
    assert resultado.loc[(2019, "con", "percentil"), "N_COMPARAVEIS_ANO_ANTERIOR"] == 0
    assert resultado.loc[(2020, "ind", "percentil"), "N_REF_ANO_ANTERIOR"] == 0
    row = resultado.loc[(2021, "con", "percentil")]
    assert row["N_REF_ANO_ANTERIOR"] == 2
    assert row["N_NORMALIZACAO_SETORIAL"] == 2
    assert row["N_FALLBACK_AMPLA"] == 1
    assert row["N_COMPARAVEIS_ANO_ANTERIOR"] == 3
    assert row["MEDIANA_ABS_ANO_ANTERIOR"] == pytest.approx(25)
    assert "CD_CVM" not in resultado.columns
