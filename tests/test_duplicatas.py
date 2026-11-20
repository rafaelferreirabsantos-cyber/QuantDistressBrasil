"""Política de seleção e linhagem na auditoria de fatos DFP."""

import pandas as pd
import pytest

from quantdistress.evaluation.duplicates import CHAVE_CONTABIL, auditar_duplicatas


def _fato(linha, conta, **campos):
    fato = {
        "CNPJ_CIA": "00.000.000/0001-00",
        "CD_CVM": "000099",
        "DT_REFER": pd.Timestamp("2024-12-31"),
        "VERSAO": 1,
        "DENOM_CIA": "Companhia de teste",
        "GRUPO_DFP": "DF Consolidado - Balanço Patrimonial Ativo",
        "MOEDA": "REAL",
        "ESCALA_MOEDA": "MIL",
        "ORDEM_EXERC": "ÚLTIMO",
        "DT_INI_EXERC": pd.NaT,
        "DT_FIM_EXERC": pd.Timestamp("2024-12-31"),
        "CD_CONTA": conta,
        "DS_CONTA": "Conta de teste",
        "VL_CONTA": "1.000000000000000000001",
        "ST_CONTA_FIXA": "S",
        "ESCOPO": "con",
        "FAMILIA": "BPA",
        "ARQUIVO_ORIGEM": "dfp_cia_aberta_BPA_con_2024.csv",
        "LINHA_ORIGEM": linha,
    }
    return {**fato, **campos}


def test_classifica_e_preserva_todos_os_conflitos_sem_inferir_valores():
    fatos = pd.DataFrame(
        [
            _fato(9, "1"),
            _fato(2, "1"),
            _fato(1, "1", ESCOPO="ind", ARQUIVO_ORIGEM="dfp_cia_aberta_BPA_ind_2024.csv"),
            _fato(10, "1", ORDEM_EXERC="PENÚLTIMO", DT_FIM_EXERC=pd.Timestamp("2023-12-31")),
            _fato(3, "1", VERSAO=2),
            _fato(11, "1.01"),
            _fato(12, "1.01", VL_CONTA="1.000000000000000000002"),
            _fato(13, "1.02"),
            _fato(14, "1.02", DS_CONTA="Rótulo concorrente"),
            _fato(15, "1.03"),
            _fato(16, "1.03", ESCALA_MOEDA="UNIDADE"),
            _fato(17, "1.04"),
            _fato(18, "1.04", VL_CONTA="2", DS_CONTA="Rótulo concorrente"),
            _fato(19, "1.05", VL_CONTA="1.0000"),
            _fato(20, "1.05", VL_CONTA="1"),
            _fato(21, "2"),
        ]
    )
    originais = fatos.copy()
    auditoria = auditar_duplicatas(fatos)

    grupos = auditoria.grupos_repetidos.set_index("CD_CONTA")
    assert grupos["CLASSE_DUPLICATA"].to_dict() == {
        "1": "exata", "1.01": "valor", "1.02": "rotulo", "1.03": "outros",
        "1.04": "mista", "1.05": "outros",
    }
    assert grupos.loc["1", "LINHA_SELECIONADA"] == 2
    assert grupos.loc["1.04", "CAMPOS_DIVERGENTES"] == "DS_CONTA,VL_CONTA"
    assert not grupos.loc["1.05", "DIFERENCA_VALOR"]
    assert grupos.loc["1.05", "DIFERENCA_OUTROS"]
    assert grupos.loc["1.05", "CAMPOS_DIVERGENTES"] == "VL_CONTA"
    assert len(auditoria.chaves_nao_resolvidas) == 5
    assert auditoria.chaves_nao_resolvidas["LINHA_SELECIONADA"].isna().all()
    assert len(auditoria.linhas_repetidas) == 12
    assert auditoria.linhas_repetidas["SELECIONADA_ANALITICA"].sum() == 1
    assert auditoria.fatos_selecionados["LINHA_ORIGEM"].tolist() == [2, 1, 10, 3, 21]
    assert not auditoria.fatos_selecionados.duplicated(list(CHAVE_CONTABIL)).any()
    pd.testing.assert_frame_equal(fatos, originais)


def test_selecao_e_independente_da_ordem_do_dataframe():
    fatos = pd.DataFrame([_fato(8, "1"), _fato(2, "1"), _fato(6, "1")])
    for quadro in [fatos, fatos.iloc[::-1]]:
        auditoria = auditar_duplicatas(quadro)
        assert auditoria.fatos_selecionados["LINHA_ORIGEM"].tolist() == [2]
        assert auditoria.grupos_repetidos["N_LINHAS"].tolist() == [3]


def test_casos_sem_repeticao_preservam_esquemas_e_fatos():
    fatos = pd.DataFrame([_fato(1, "1")])
    auditoria = auditar_duplicatas(fatos)
    assert auditoria.grupos_repetidos.empty
    assert auditoria.linhas_repetidas.empty
    assert auditoria.chaves_nao_resolvidas.empty
    pd.testing.assert_frame_equal(auditoria.fatos_selecionados, fatos)


def test_marcacao_bruta_impede_que_normalizacao_dissimule_divergencia():
    fatos = pd.DataFrame(
        [_fato(1, "1", FATO_REPETIDO=False), _fato(2, "1", FATO_REPETIDO=False)]
    )
    auditoria = auditar_duplicatas(fatos)
    assert auditoria.fatos_selecionados.empty
    pendentes = auditoria.chaves_nao_resolvidas
    assert pendentes["CLASSE_DUPLICATA"].tolist() == ["outros"]
    assert pendentes["CAMPOS_DIVERGENTES"].tolist() == ["FATO_REPETIDO"]


def test_chave_repetida_incompleta_fica_pendente_mas_registro_unico_e_preservado():
    fatos = pd.DataFrame(
        [
            _fato(1, "1", VERSAO=pd.NA),
            _fato(2, "1", VERSAO=pd.NA),
            _fato(3, "2", VERSAO=pd.NA),
            _fato(4, "3.01", FAMILIA="DRE"),
            _fato(5, "3.01", FAMILIA="DRE"),
        ]
    )
    auditoria = auditar_duplicatas(fatos)
    pendentes = auditoria.chaves_nao_resolvidas
    assert pendentes["CD_CONTA"].tolist() == ["1", "3.01"]
    assert pendentes["CLASSE_DUPLICATA"].eq("exata").all()
    assert not pendentes["CHAVE_COMPLETA"].any()
    assert auditoria.fatos_selecionados["LINHA_ORIGEM"].tolist() == [3]


def test_linhagem_fisica_ambigua_falha_em_vez_de_escolher_a_posicao():
    fatos = pd.DataFrame([_fato(1, "1"), _fato(1, "2")])
    with pytest.raises(ValueError, match="linhagem física"):
        auditar_duplicatas(fatos)
