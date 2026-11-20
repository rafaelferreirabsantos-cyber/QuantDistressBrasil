import pandas as pd
import pytest

from quantdistress.evaluation.matrix03b import contar_matriz
from quantdistress.evaluation.sensitivity03b import analisar_sensibilidade, quadrantes


def _amostra():
    return pd.DataFrame({
        "ANO_ARQUIVO": [2024, 2024, 2024, 2024], "CD_CVM": ["1", "2", "3", "1"],
        "CNPJ_CIA": ["01", "02", "03", "01"], "ESCOPO": ["con", "con", "con", "ind"],
        "SETOR_FCA": ["Teste"] * 4, "DT_REFER": pd.Timestamp("2024-12-31"),
        "QUALITY_SCORE": [49.0, 10.0, 100.0, 50.0], "FINANCIAL_DISTRESS_SCORE": [50.0, 20.0, None, 100.0],
        "MODO_TEMPORAL": "descritivo_revisado",
    })


def test_quadrantes_sao_geometricos_e_preservam_ausencia():
    q = pd.Series([0.0, 50.0, 100.0, None, 50 - 1e-14])
    d = pd.Series([50.0, 0.0, 100.0, 40.0, 49.0])
    faixas = quadrantes(q, d, 50)
    assert faixas[:3].tolist() == ["Q<·D≥", "Q≥·D<", "Q≥·D≥"]
    assert pd.isna(faixas[3])
    assert faixas[4] == "Q≥·D<"


def test_pareamento_distingue_perda_de_cobertura_de_mudanca_de_quadrante():
    base = _amostra()
    alternativa = base.copy()
    alternativa.loc[0, "QUALITY_SCORE"] = 51
    alternativa.loc[1, "QUALITY_SCORE"] = None
    r = analisar_sensibilidade(base, {"alternativa": alternativa}, "exato")
    quad = r["estabilidade_quadrantes"].query(
        "NIVEL == 'periodo_escopo' and ESCOPO == 'con' and CENARIO == 'alternativa' and CORTE_BASE == 50"
    ).iloc[0]
    assert (quad.PAREADAS, quad.SO_BASE, quad.MUDARAM, quad.PROPORCAO_MUDANCA) == (1, 1, 1, 1)
    pares = r["sensibilidade_scores"].query("NIVEL == 'periodo_escopo' and ESCOPO == 'con'")
    assert pares.set_index("EIXO")["PAREADAS"].to_dict() == {"QUALITY_SCORE": 2, "FINANCIAL_DISTRESS_SCORE": 2}
    mudanca_corte = r["estabilidade_quadrantes"].query(
        "NIVEL == 'periodo_escopo' and ESCOPO == 'con' and CENARIO == 'convencao_corte' and CORTE_CENARIO == 40"
    ).iloc[0]
    assert mudanca_corte.PAREADAS == 2 and mudanca_corte.MUDARAM == 1


def test_pesos_e_metodo_geram_a_mesma_amostra_tripla_por_eixo():
    base = _amostra()
    pesos = base.copy()
    metodo = base.copy()
    metodo.loc[0, "QUALITY_SCORE"] = None
    r = analisar_sensibilidade(base, {"pesos_economicos": pesos, "z_robusto": metodo}, "exato")
    q = r["sensibilidade_scores"].query(
        "NIVEL == 'periodo_escopo' and ESCOPO == 'con' and EIXO == 'QUALITY_SCORE'"
    ).set_index(["CENARIO", "AMOSTRA"])
    assert q.loc[("pesos_economicos", "pares_por_cenario"), "PAREADAS"] == 3
    assert q.loc[("pesos_economicos", "comum_benchmark_pesos_metodo"), "PAREADAS"] == 2
    assert q.loc[("z_robusto", "comum_benchmark_pesos_metodo"), "PAREADAS"] == 2


def test_pareamento_bloqueia_mudanca_de_identidade_e_modo_temporal():
    base = _amostra()
    alternativa = base.copy()
    alternativa.loc[0, "CNPJ_CIA"] = "outro"
    with pytest.raises(ValueError, match="CNPJ_CIA"):
        analisar_sensibilidade(base, {"alternativa": alternativa}, "exato")
    with pytest.raises(ValueError, match="descritivo_revisado"):
        contar_matriz(base.assign(MODO_TEMPORAL="historico"))


def test_matriz_preserva_escopo_inclui_cem_na_borda_e_usa_so_os_dois_eixos():
    matriz = contar_matriz(_amostra()).loc[lambda x: x.ANO_ARQUIVO.isna()]
    assert matriz.groupby("ESCOPO").OBSERVACOES.sum().to_dict() == {"con": 2, "ind": 1}
    borda = matriz.query("ESCOPO == 'ind' and QUALITY_DE == 50 and DISTRESS_DE == 90")
    assert borda.OBSERVACOES.item() == 1
