import json

import pandas as pd
import pytest

from quantdistress.evaluation.diagnostics03 import _identidade_ativos, diagnosticar_indicadores, matriz_indicadores

MARGEM = "margem_operacional"
LIQUIDEZ = "liquidez_corrente"


def _linha(ano, codigo, medida, valor, *, escopo="con", setor="Alimentos", situacao="valido", divisor="100"):
    conceito = "receita_vendas_servicos" if medida == MARGEM else "passivo_circulante"
    return {
        "ANO_ARQUIVO": ano,
        "CNPJ_CIA": f"{codigo:014d}",
        "CD_CVM": str(codigo),
        "DT_REFER": pd.Timestamp(ano, 12, 31),
        "VERSAO": 1,
        "ESCOPO": escopo,
        "GRUPO_SETORIAL": "nao_financeira",
        "SETOR_FCA": setor,
        "INDICADOR": medida,
        "VALOR": valor,
        "SITUACAO": situacao,
        "FONTES": json.dumps([{
            "CONCEITO": conceito, "ORDEM_EXERC": "ÚLTIMO", "ESCALA_MOEDA": "MIL", "VL_CONTA": divisor,
        }]),
    }


def test_cobertura_conjunta_distingue_emissor_repetido_ano_e_escopo():
    dados = pd.DataFrame([
        _linha(2024, 1, MARGEM, .4),
        _linha(2024, 1, LIQUIDEZ, 1.3),
        _linha(2025, 1, MARGEM, .5),
        _linha(2025, 1, MARGEM, .7, escopo="ind"),
        _linha(2025, 2, MARGEM, None, setor=None, situacao="setor_nao_classificado"),
    ])
    resultados = diagnosticar_indicadores(dados)
    margem = resultados["cobertura_indicadores"].query("NIVEL == 'periodo' and INDICADOR == @MARGEM")
    cobertura = margem.set_index("ESCOPO")
    assert cobertura.loc["con", "OBSERVACOES_VALIDAS"] == 2
    assert cobertura.loc["con", "EMISSORES_VALIDOS"] == 1
    assert cobertura.loc["ind", "OBSERVACOES_VALIDAS"] == 1
    perfis = resultados["cobertura_conjunta"].query("NIVEL == 'periodo' and ESCOPO == 'con'")
    assert set(zip(perfis["N_QUALITY"], perfis["N_DISTRESS"])) == {(0, 0), (1, 0), (1, 1)}
    por_setor = resultados["cobertura_indicadores"].query("NIVEL == 'ano_setor'")
    assert por_setor["SETOR_FCA"].isna().any()


def test_denominador_zero_e_negativo_vem_da_linhagem_e_falha_anterior_e_separada():
    dados = pd.DataFrame([
        _linha(2024, 1, MARGEM, None, situacao="denominador_invalido", divisor="0.000"),
        _linha(2024, 2, MARGEM, None, situacao="denominador_invalido", divisor="-0.00000001"),
        _linha(2024, 3, MARGEM, None, situacao="periodo_incompativel", divisor="0"),
        _linha(2024, 4, MARGEM, 0),
    ])
    contagem = diagnosticar_indicadores(dados)["denominadores"].query("NIVEL == 'periodo'")
    assert contagem.set_index("TIPO_DENOMINADOR")["OBSERVACOES"].to_dict() == {
        "zero": 1, "negativo": 1, "divisao_nao_avaliada": 1, "positivo": 1,
    }


def test_correlacao_usa_pares_ranks_medios_e_suprime_grupo_constante():
    dados = pd.DataFrame([
        _linha(2024, codigo, medida, valor)
        for codigo, x, y in [(1, .2, 4), (2, .2, 4), (3, .3, 2), (4, .7, 0)]
        for medida, valor in [(MARGEM, x), (LIQUIDEZ, y)]
    ] + [_linha(2024, 5, MARGEM, 10)])
    filtro = "NIVEL == 'periodo' and INDICADOR_X == @MARGEM and INDICADOR_Y == @LIQUIDEZ"
    correlacao = diagnosticar_indicadores(dados, minimo_correlacao=4)["correlacoes"].query(filtro).iloc[0]
    assert correlacao["OBSERVACOES_PAREADAS"] == 4
    assert correlacao["EMISSORES_PAREADOS"] == 4
    assert correlacao["SPEARMAN"] == pytest.approx(-1)
    dados.loc[dados["INDICADOR"].eq(LIQUIDEZ), "VALOR"] = 1
    resultados = diagnosticar_indicadores(dados, minimo_correlacao=4)["correlacoes"]
    assert resultados.query(filtro).iloc[0]["MOTIVO"] == "serie_constante"


def test_matriz_recusa_duplicatas_ou_valor_marcado_invalido():
    observacao = _linha(2024, 1, MARGEM, .4)
    with pytest.raises(ValueError, match="duplicado"):
        matriz_indicadores(pd.DataFrame([observacao, observacao]))
    with pytest.raises(ValueError, match="validade"):
        matriz_indicadores(pd.DataFrame([{**observacao, "SITUACAO": "conta_ausente"}]))
    with pytest.raises(ValueError, match="validade"):
        matriz_indicadores(pd.DataFrame([{**observacao, "SITUACAO": "conta_ausente", "VALOR": float("inf")}]))


def test_identidade_margem_giro_conta_tripla_e_emissor_separadamente():
    quadro = pd.DataFrame({
        "CD_CVM": ["1", "1", "2"],
        "rentabilidade_operacional_ativos": [.15, .7, pd.NA],
        "margem_operacional": [.3, .25, .3],
        "giro_ativo": [.5, 2, .5],
    })
    resultado = _identidade_ativos(quadro)
    assert resultado["OBSERVACOES_TRIPLA"] == 2
    assert resultado["EMISSORES_TRIPLA"] == 1
    assert resultado["FORA_DA_TOLERANCIA"] == 1
    assert resultado["ERRO_ABSOLUTO_MAXIMO"] == pytest.approx(.2)
