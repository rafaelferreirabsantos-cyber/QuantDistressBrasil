import json

import pandas as pd

from quantdistress.evaluation.feasibility03 import (
    CHAVE,
    D_NUCLEO,
    D_TODOS,
    PRESSAO,
    Q_NUCLEO,
    Q_TODOS,
    _cobertura_pares_exatos,
    _extrair_experimentos,
    _resumir_grupos,
    cenarios_cobertura,
    selecionar_referencias,
)


def test_referencia_unica_preserva_anos_e_escopos_e_bloqueia_empates():
    base = pd.DataFrame([
        [2020, "1", "con", "2020-02-28"], [2020, "1", "con", "2020-12-31"],
        [2021, "1", "con", "2021-12-31"], [2021, "1", "ind", "2021-12-31"],
        [2021, "2", "con", "2021-06-30"], [2021, "2", "con", "2021-12-31"],
        [2021, "2", "con", "2021-12-31"],
    ], columns=["ANO_ARQUIVO", "CD_CVM", "ESCOPO", "DT_REFER"])
    base["DT_REFER"] = pd.to_datetime(base["DT_REFER"])
    assert selecionar_referencias(base).tolist() == [False, True, True, True, False, False, False]


def test_percentual_generico_nao_substitui_nucleo_e_caixa_zero_nao_imputa_razao():
    quadro = pd.DataFrame(1.0, index=range(2), columns=[*Q_TODOS, *D_TODOS])
    quadro.loc[0, Q_NUCLEO[0]] = pd.NA
    quadro.loc[1, PRESSAO] = pd.NA
    casos = cenarios_cobertura(quadro, pd.Series([False, True]))
    assert casos["q_4_de_5_quaisquer"].tolist() == [True, True]
    assert casos["q_nucleo_2_de_2"].tolist() == [False, True]
    assert casos["d_nucleo_3_de_3"].all()
    assert casos["d_nucleo_mais_pressao_ou_estado_caixa_zero"].all()
    assert casos["d_4_de_4"].tolist() == [True, False]
    assert pd.isna(quadro.loc[1, PRESSAO])


def test_denominadores_e_variantes_respeitam_escala_original():
    chave = [2024, "00.000.000/0001-00", "1", pd.Timestamp("2024-12-31"), 1, "con"]
    maior = {"VL_CONTA": "12", "ESCALA_MOEDA": "MIL"}
    menor = {"VL_CONTA": "500", "ESCALA_MOEDA": "UNIDADE"}
    zero = {"VL_CONTA": "0", "ESCALA_MOEDA": "MIL"}
    base = pd.DataFrame([
        [*chave, PRESSAO, "denominador_invalido", None, json.dumps([menor, zero])],
        [*chave, "rentabilidade_operacional_ativos", "valido", .05, json.dumps([menor, maior, maior])],
    ], columns=[*CHAVE, "INDICADOR", "SITUACAO", "VALOR", "FONTES"])
    caixa, alternativas, _ = _extrair_experimentos(base)
    assert caixa["ESTADO_CAIXA_ZERO"].iloc[0] == "com_financiamento"
    assert alternativas["ALTERNATIVA"].iloc[0] == 500 / 12_000


def test_contagem_periodo_separa_emissor_de_referencia_anual():
    base = pd.DataFrame({
        "ANO_ARQUIVO": [2020, 2021], "CD_CVM": ["1", "1"], "ESCOPO": ["con", "con"],
        "GRUPO_SETORIAL": ["nao_financeira"] * 2, "SETOR_FCA": ["Alimentos"] * 2, "PORTA": [True, True],
    })
    periodo = _resumir_grupos(base, ["PORTA"]).query("NIVEL == 'periodo_escopo'").iloc[0]
    assert periodo["PORTA"] == 2 and periodo["EMISSORES_PORTA"] == 1


def test_pares_excluem_alvo_e_referencia_constante_apos_exclusao():
    n = 16
    base = pd.DataFrame({
        "ANO_ARQUIVO": [2020] * n, "CD_CVM": [str(i) for i in range(n)], "ESCOPO": ["con"] * n,
        "GRUPO_SETORIAL": ["nao_financeira"] * n, "SETOR_FCA": ["Alimentos"] * n,
        **{nome: list(range(n)) for nome in (*Q_NUCLEO, *D_NUCLEO)},
    })
    base[Q_NUCLEO[0]] = [0] * 15 + [1]
    resumo = _cobertura_pares_exatos(base).query("NIVEL == 'periodo_escopo'").set_index("MIN_PARES_EXCLUINDO_ALVO")
    assert resumo.loc[15, "AMBOS_PARES"] == 15
    assert resumo.loc[30, "AMBOS_PARES"] == 0
