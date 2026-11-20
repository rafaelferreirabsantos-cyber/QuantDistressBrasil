import json

import pandas as pd
import pytest

from quantdistress.features.indicators import CHAVE_PAINEL, calcular_indicadores


@pytest.fixture
def entrega_2024():
    contexto = {
        "CNPJ_CIA": "00.000.000/0001-00",
        "CD_CVM": "000001",
        "DT_REFER": pd.Timestamp("2024-12-31"),
        "VERSAO": 2,
        "ESCOPO": "con",
    }
    linhas = []

    def conta(familia, codigo, rotulo, valor, *, anterior=False, escala="MIL"):
        ano = 2023 if anterior else 2024
        possui_fluxo = familia not in ("BPA", "BPP")
        linhas.append({
            **contexto,
            "FAMILIA": familia,
            "CD_CONTA": codigo,
            "DS_CONTA": rotulo,
            "VL_CONTA": valor,
            "ST_CONTA_FIXA": "S",
            "MOEDA": "REAL",
            "ESCALA_MOEDA": escala,
            "FATOR_ESCALA_MOEDA": 1_000 if escala == "MIL" else 1,
            "ORDEM_EXERC": "PENÚLTIMO" if anterior else "ÚLTIMO",
            "DT_INI_EXERC": pd.Timestamp(ano, 1, 1) if possui_fluxo else pd.NaT,
            "DT_FIM_EXERC": pd.Timestamp(ano, 12, 31),
            "ARQUIVO_ORIGEM": f"dfp_{familia.lower()}_con_2024.csv",
            "LINHA_ORIGEM": len(linhas) + 1,
            "ID_DOC": "200",
            "SITUACAO_VINCULO": "unico",
        })

    conta("BPA", "1", "Ativo Total", "12")
    conta("BPA", "1", "Ativo Total", "8", anterior=True)
    conta("BPA", "1.01", "Ativo Circulante", "3")
    conta("BPA", "1.01.01", "Caixa e Equivalentes de Caixa", "0.8")
    conta("BPP", "2.01", "Passivo Circulante", "4")
    conta("BPP", "2.01.04", "Empréstimos e Financiamentos", "1800", escala="UNIDADE")
    conta("BPP", "2.02.01", "Empréstimos e Financiamentos", "2.5")
    conta("BPP", "2.03", "Patrimônio Líquido Consolidado", "-1")
    conta("DRE", "3.01", "Receita de Venda de Bens e/ou Serviços", "6")
    conta("DRE", "3.01", "Receita de Venda de Bens e/ou Serviços", "5", anterior=True)
    conta("DRE", "3.05", "Resultado Antes do Resultado Financeiro e dos Tributos", "-1.5")
    conta("DFC_MI", "6.01", "Caixa Líquido das Atividades Operacionais", "-3")
    universo = pd.DataFrame([{**contexto, "GRUPO_SETORIAL": "nao_financeira"}])
    return pd.DataFrame(linhas), universo


def test_prototipos_preservam_sinais_escalas_e_linhagem(entrega_2024):
    fatos, universo = entrega_2024
    resultado = calcular_indicadores(fatos, universo).set_index("INDICADOR")

    assert resultado["SITUACAO"].eq("valido").all()
    assert resultado["VALOR"].to_dict() == pytest.approx({
        "margem_operacional": -0.25,
        "rentabilidade_operacional_ativos": -0.15,
        "fluxo_caixa_operacional_sobre_receita": -0.5,
        "giro_ativo": 0.6,
        "crescimento_receita": 0.2,
        "liquidez_corrente": 0.75,
        "patrimonio_liquido_sobre_ativo": -1 / 12,
        "financiamentos_reportados_sobre_ativo": 4.3 / 12,
        "financiamentos_circulantes_sobre_caixa": 2.25,
    })
    fontes = json.loads(resultado.loc["financiamentos_circulantes_sobre_caixa", "FONTES"])
    assert [fonte["CD_CONTA"] for fonte in fontes] == ["2.01.04", "1.01.01"]
    assert fontes[0]["ESCALA_MOEDA"] == "UNIDADE"
    assert fontes[0]["LINHA_ORIGEM"] == 6
    assert fontes[0]["ARQUIVO_ORIGEM"] == "dfp_bpp_con_2024.csv"
    assert fontes[0]["ID_DOC"] == "200"
    assert fontes[0]["DT_INI_EXERC"] is None
    assert fontes[0]["DT_FIM_EXERC"] == "2024-12-31"


@pytest.mark.parametrize(
    ("coluna", "valor", "situacao"),
    [
        ("DS_CONTA", "Receitas de Intermediação Financeira", "conceito_nao_validado"),
        ("ST_CONTA_FIXA", "N", "conceito_nao_validado"),
        ("MOEDA", "DOLAR", "moeda_escala_invalida"),
        ("FATOR_ESCALA_MOEDA", 1, "moeda_escala_invalida"),
        ("VL_CONTA", "0", "denominador_invalido"),
        ("VL_CONTA", "-1", "denominador_invalido"),
        ("VL_CONTA", pd.NA, "valor_ausente"),
        ("DT_INI_EXERC", pd.Timestamp("2024-04-01"), "periodo_incompativel"),
        ("DT_FIM_EXERC", pd.Timestamp("2024-12-30"), "periodo_incompativel"),
        ("ID_DOC", "999", "vinculo_invalido"),
    ],
)
def test_invalida_receita_incompativel_sem_imputar(entrega_2024, coluna, valor, situacao):
    fatos, universo = entrega_2024
    receita = fatos["CD_CONTA"].eq("3.01") & fatos["ORDEM_EXERC"].eq("ÚLTIMO")
    fatos.loc[receita, coluna] = valor
    saida = calcular_indicadores(fatos, universo).set_index("INDICADOR")

    assert saida.loc["margem_operacional", "SITUACAO"] == situacao
    assert pd.isna(saida.loc["margem_operacional", "VALOR"])
    assert saida.loc["liquidez_corrente", "SITUACAO"] == "valido"


def test_comparativos_de_outro_escopo_ou_versao_nao_preenchem_resultados(entrega_2024):
    fatos, universo = entrega_2024
    bpa_passado = fatos["CD_CONTA"].eq("1") & fatos["ORDEM_EXERC"].eq("PENÚLTIMO")
    receita_passada = fatos["CD_CONTA"].eq("3.01") & fatos["ORDEM_EXERC"].eq("PENÚLTIMO")
    fatos.loc[bpa_passado, "ESCOPO"] = "ind"
    fatos.loc[receita_passada, "VERSAO"] = 1
    resultado = calcular_indicadores(fatos, universo).set_index("INDICADOR")["SITUACAO"]

    assert resultado["rentabilidade_operacional_ativos"] == "conta_ausente"
    assert resultado["crescimento_receita"] == "conta_ausente"
    assert resultado["patrimonio_liquido_sobre_ativo"] == "valido"


def test_rejeita_saldo_inicial_e_fluxo_comparativo_que_nao_alinham(entrega_2024):
    fatos, universo = entrega_2024
    bpa_passado = fatos["CD_CONTA"].eq("1") & fatos["ORDEM_EXERC"].eq("PENÚLTIMO")
    receita_passada = fatos["CD_CONTA"].eq("3.01") & fatos["ORDEM_EXERC"].eq("PENÚLTIMO")
    fatos.loc[bpa_passado | receita_passada, "DT_FIM_EXERC"] = pd.Timestamp("2023-12-30")
    fatos.loc[receita_passada, "DT_INI_EXERC"] = pd.Timestamp("2022-12-31")
    resultado = calcular_indicadores(fatos, universo).set_index("INDICADOR")["SITUACAO"]

    assert resultado["rentabilidade_operacional_ativos"] == "periodo_incompativel"
    assert resultado["crescimento_receita"] == "periodo_incompativel"


def test_mantem_escopos_setores_e_entregas_sem_fatos_no_denominador(entrega_2024):
    fatos, base = entrega_2024
    universo = pd.concat([
        base,
        base.assign(ESCOPO="ind"),
        base.assign(CD_CVM="000002", GRUPO_SETORIAL="financeira"),
        base.assign(CD_CVM="000003", GRUPO_SETORIAL="nao_classificada"),
        base.assign(CD_CVM="000004", GRUPO_SETORIAL="regime_especifico"),
    ], ignore_index=True)
    resultado = calcular_indicadores(fatos, universo)

    situacoes = resultado.groupby(["CD_CVM", "ESCOPO"])["SITUACAO"].unique()
    assert situacoes[("000001", "con")].tolist() == ["valido"]
    assert situacoes[("000001", "ind")].tolist() == ["sem_fatos"]
    assert situacoes[("000002", "con")].tolist() == ["setor_nao_elegivel"]
    assert situacoes[("000003", "con")].tolist() == ["setor_nao_classificado"]
    assert situacoes[("000004", "con")].tolist() == ["setor_nao_elegivel"]


def test_conflito_auditado_e_duas_dfcs_bloqueiam_apenas_seus_indicadores(entrega_2024):
    fatos, universo = entrega_2024
    passivo = fatos["CD_CONTA"].eq("2.01")
    conflitos = fatos.loc[passivo, [*CHAVE_PAINEL, "FAMILIA", "CD_CONTA", "ORDEM_EXERC"]]
    selecionados = pd.concat([
        fatos.loc[~passivo], fatos.loc[fatos["FAMILIA"].eq("DFC_MI")].assign(FAMILIA="DFC_MD"),
    ], ignore_index=True)
    resultado = calcular_indicadores(selecionados, universo, conflitos=conflitos)
    situacoes = resultado.set_index("INDICADOR")["SITUACAO"]

    assert situacoes["liquidez_corrente"] == "conflito_contabil"
    assert situacoes["fluxo_caixa_operacional_sobre_receita"] == "conflito_contabil"
    assert situacoes["margem_operacional"] == "valido"


def test_caixa_zero_e_financiamentos_ausentes_tem_situacoes_distintas(entrega_2024):
    fatos, universo = entrega_2024
    fatos.loc[fatos["CD_CONTA"].eq("1.01.01"), "VL_CONTA"] = "0"
    fatos = fatos.loc[fatos["CD_CONTA"].ne("2.02.01")]
    situacoes = calcular_indicadores(fatos, universo).set_index("INDICADOR")["SITUACAO"]

    assert situacoes["financiamentos_circulantes_sobre_caixa"] == "denominador_invalido"
    assert situacoes["financiamentos_reportados_sobre_ativo"] == "conta_ausente"
