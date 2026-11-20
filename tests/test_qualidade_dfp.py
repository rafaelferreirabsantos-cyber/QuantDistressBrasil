from decimal import Decimal

import pandas as pd

from quantdistress.evaluation.quality import (
    CHAVE_ENTREGA,
    cobertura_por_escopo,
    conciliacao_patrimonial,
)


def test_cobertura_conta_uma_chave_por_escopo_e_separa_fatos_sem_indice():
    chave = ["01.001.001/0001-00", "1", pd.Timestamp("2024-12-31"), 1]
    outra = ["02.002.002/0001-00", "2", pd.Timestamp("2024-12-31"), 1]
    entregas = pd.DataFrame([chave, chave], columns=CHAVE_ENTREGA)
    fatos = pd.DataFrame(
        [
            *([*chave, "con", "ÚLTIMO", familia]
              for familia in ("BPA", "BPP", "DRE", "DFC_MD", "DFC_MI")),
            [*chave, "ind", "PENÚLTIMO", "BPA"],
            [*outra, "ind", "ÚLTIMO", "BPA"],
        ],
        columns=[*CHAVE_ENTREGA, "ESCOPO", "ORDEM_EXERC", "FAMILIA"],
    )

    cobertura = cobertura_por_escopo(fatos, entregas)

    assert cobertura.loc["con", "TOTAL_CHAVES_NO_INDICE"] == 1
    assert cobertura.loc["con", "BPA_BPP_DRE_DFC"] == 1
    assert cobertura.loc["con", "AMBOS_METODOS_DFC"] == 1
    assert cobertura.loc["ind", "SEM_DEMONSTRACAO_NO_ESCOPO"] == 1
    assert cobertura.loc["ind", "COM_DEMONSTRACAO_FORA_DO_INDICE"] == 1


def test_conciliacao_preserva_escopo_periodo_e_conflito_de_totais():
    fim = pd.Timestamp("2024-12-31")
    chave = ["01.001.001/0001-00", "1", fim, 1]
    colunas = [
        *CHAVE_ENTREGA, "ESCOPO", "ORDEM_EXERC", "DT_INI_EXERC", "DT_FIM_EXERC",
        "FAMILIA", "CD_CONTA", "MOEDA", "VL_CONTA", "FATOR_ESCALA_MOEDA",
    ]
    con = [*chave, "con", "ÚLTIMO", pd.NaT, fim]
    ind = [*chave, "ind", "ÚLTIMO", pd.NaT, fim]
    ativo = ["BPA", "1", "REAL", "1.005", 1000]
    fatos = pd.DataFrame(
        [
            [*con, *ativo],
            [*con, *ativo],
            [*con, "BPP", "2", "REAL", "1000.0", 1],
            [*ind, *ativo],
            [*ind, "BPA", "1", "REAL", "2", 1000],
            [*ind, "BPP", "2", "REAL", "1000.0", 1],
        ],
        columns=colunas,
    )

    pares = conciliacao_patrimonial(fatos).set_index("ESCOPO")

    assert pares.loc["con", "SITUACAO"] == "dentro_da_tolerancia"
    assert pares.loc["con", "DIFERENCA_EM_UNIDADES"] == Decimal("5")
    assert pares.loc["con", "TOLERANCIA_EM_UNIDADES"] == 1000
    assert pares.loc["ind", "SITUACAO"] == "multiplos_totais"
    assert pd.isna(pares.loc["ind", "DIFERENCA_EM_UNIDADES"])
