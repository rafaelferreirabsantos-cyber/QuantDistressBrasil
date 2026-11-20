import json

import pandas as pd
import pytest

from quantdistress.evaluation.feasibility03 import D_NUCLEO, Q_NUCLEO
from quantdistress.evaluation.revision03 import MACROSETORES, carregar_painel, cenarios_referencia, experimentar_revisao
from quantdistress.features.indicators import PROTOTIPOS


def _observacoes(setor, codigos, *, escopo="con", ano=2024):
    for valor, cvm in enumerate(codigos):
        for indicador in (*Q_NUCLEO, *D_NUCLEO):
            fontes = [
                {"CONCEITO": conceito, "ID_DOC": cvm, "ARQUIVO_ORIGEM": "fonte.csv", "LINHA_ORIGEM": 1}
                for conceito, _ in PROTOTIPOS[indicador].insumos
            ]
            yield {
                "ANO_ARQUIVO": ano, "ESCOPO": escopo, "SETOR_FCA": setor, "CD_CVM": cvm,
                "INDICADOR": indicador, "SITUACAO": "valido", "VALOR": valor, "ID_DOC": cvm,
                "FONTES": json.dumps(fontes), "DT_DIVULGACAO": pd.NaT,
            }


def test_macro_preserva_exato_e_recupera_apenas_setores_mapeados_sem_cruzar_escopos():
    energia, saneamento = MACROSETORES["utilidades"]
    base = pd.DataFrame([
        *_observacoes(energia, ["1", "2", "3"]),
        *_observacoes(saneamento, ["4", "5", "6", "7"]),
        *_observacoes(energia, ["8", "9", "10"], escopo="ind"),
        *_observacoes("Comércio (Atacado e Varejo)", ["11", "12", "13"]),
    ])
    resultado = experimentar_revisao(base, min_pares=3)
    contagem = resultado["cobertura_macrosetores"].query("NIVEL == 'periodo_escopo'").set_index(["ESCOPO", "REFERENCIA"])
    assert contagem.loc[("con", "setor_exato"), "AMBOS"] == 4
    assert contagem.loc[("con", "utilidades"), "AMBOS"] == 7
    assert contagem.loc[("con", "utilidades"), "RECUPERADAS"] == 3
    assert contagem.loc[("con", "amplo_exploratorio"), "RECUPERADAS"] == 6
    assert contagem.loc[("ind", "macros_candidatos"), "AMBOS"] == 0
    assert all("CD_CVM" not in tabela for tabela in resultado.values())


def test_quatro_dimensoes_independentes_em_conta_ausente_e_linhagem_incompleta():
    base = pd.DataFrame(_observacoes("Setor de teste", ["1", "2", "3", "4", "5"]))
    afetado = base["CD_CVM"].eq("1") & base["INDICADOR"].eq(Q_NUCLEO[0])
    base.loc[afetado, ["SITUACAO", "VALOR"]] = ["conta_ausente", None]
    incompleto = base["CD_CVM"].eq("2") & base["INDICADOR"].eq(Q_NUCLEO[0])
    base.loc[incompleto, "FONTES"] = "[]"
    base.loc[incompleto, "DT_DIVULGACAO"] = pd.Timestamp("2025-04-01")
    quadro = experimentar_revisao(base, min_pares=2)["suporte_componentes"].set_index("A_CONTABIL")
    assert not quadro.loc["conta_ausente", "DISPONIVEL"]
    assert quadro.loc["conta_ausente", "S_ESTATISTICO"] == "utilizavel"
    assert quadro.loc["linhagem_incompleta", "DISPONIVEL"]
    assert quadro.loc["linhagem_incompleta", "DATA_DIVULGACAO"] == "informada_sem_verificacao"


def test_choques_mudam_apenas_a_referencia_prevista_e_sao_reproduziveis():
    ref = pd.Series(range(10), index=list("abcdefghij"), dtype=float)
    fonte_alternativa = pd.Series([5., 6., 7.], index=["b", "p", "q"])
    cenarios = cenarios_referencia(ref, fonte_alternativa, fonte_alternativa, [*ref.index, "p"], (2024, "con", "A", "x"))
    entrada, ids = cenarios["entrada"]
    assert len(entrada) == 11 and ids.tolist() == ["q"]
    assert len(cenarios["saida"][0]) == 8
    assert len(cenarios["composicao_macro"][0]) == 10 and "q" in cenarios["composicao_macro"][0]
    assert not cenarios["valores_intermediarios"][0].equals(ref)
    assert ref.tolist() == list(range(10))
    reexecucao = cenarios_referencia(ref, fonte_alternativa, fonte_alternativa, [*ref.index, "p"], (2024, "con", "A", "x"))
    pd.testing.assert_series_equal(cenarios["saida"][0], reexecucao["saida"][0])


def test_revisao_exige_painel_descritivo_revisado(tmp_path):
    (tmp_path / "manifesto.json").write_text('{"modo_temporal":"outro_modo"}', encoding="utf-8")
    with pytest.raises(ValueError, match="descritivo revisado"):
        carregar_painel(tmp_path)
