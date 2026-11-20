import csv
from zipfile import ZipFile

import pandas as pd
import pytest

from quantdistress.data.dfp import CHAVE_ENTREGA, _ler_csv
from quantdistress.data.history import resumir_versoes


def test_aspas_legadas_preservam_rotulo_e_informam_linha_fisica(tmp_path):
    caminho = tmp_path / "historico.zip"
    colunas = ("CD_CVM", "CD_CONTA", "DS_CONTA", "VL_CONTA")
    texto = (
        'CD_CVM;CD_CONTA;DS_CONTA;VL_CONTA\r\n'
        '0123;2.03.02.13;"Senior Notes" Reestruturados;3719.0000000000\r\n'
        '0123;2.03.02.14;"Outro rótulo; com delimitador";100.0000000000\r\n'
    )
    membro_legado = "dfp_cia_aberta_BPP_con_2019.csv"
    membro_recente = "dfp_cia_aberta_BPP_con_2024.csv"
    with ZipFile(caminho, "w") as z:
        z.writestr(membro_legado, texto.encode("latin-1"))
        z.writestr(membro_recente, texto.encode("latin-1"))

    with ZipFile(caminho) as z:
        fatos, reparos = _ler_csv(z, membro_legado, colunas)
        with pytest.raises(csv.Error):
            _ler_csv(z, membro_recente, colunas)

    assert reparos == [2]
    assert fatos["DS_CONTA"].tolist() == [
        '"Senior Notes" Reestruturados', "Outro rótulo; com delimitador"
    ]
    assert fatos["VL_CONTA"].tolist() == ["3719.0000000000", "100.0000000000"]


def test_inventario_distingue_fatos_anteriores_ausentes_e_sem_indice():
    referencia = pd.Timestamp("2024-12-31")
    primeira_entrega = pd.Timestamp("2025-03-30")
    ultima_entrega = pd.Timestamp("2025-05-01")
    revisado = ["001", "01", referencia]
    revisado_com_fato_antigo = ["002", "02", referencia]
    ausente = ["003", "03", referencia]
    entregas = pd.DataFrame(
        [
            [*revisado, 1, primeira_entrega],
            [*revisado, 2, ultima_entrega],
            [*revisado, 2, ultima_entrega],
            [*revisado_com_fato_antigo, 1, primeira_entrega],
            [*revisado_com_fato_antigo, 2, ultima_entrega],
            [*ausente, 1, ultima_entrega],
            [None, "04", referencia, 1, ultima_entrega],
        ],
        columns=[*CHAVE_ENTREGA, "DT_RECEB"],
    )
    fatos = pd.DataFrame(
        [
            [*revisado, 2],
            [*revisado, 2],
            [*revisado_com_fato_antigo, 1],
            [*revisado_com_fato_antigo, 2],
            ["005", "05", referencia, 1],
            [None, "04", referencia, 1],
        ],
        columns=CHAVE_ENTREGA,
    )

    inventario = resumir_versoes(entregas, fatos)

    assert inventario["chaves_indice"] == 5
    assert inventario["linhas_indice_chave_incompleta"] == 1
    assert inventario["periodos_indice_com_multiplas_versoes"] == 2
    assert inventario["linhas_por_versao_indice"] == {"1": 3, "2": 3}
    assert inventario["chaves_fatos"] == 4
    assert inventario["linhas_fatos_chave_incompleta"] == 1
    assert inventario["chaves_fatos_sem_indice"] == 1
    assert inventario["chaves_maximas_com_fatos"] == 2
    assert inventario["chaves_maximas_sem_fatos"] == 1
    assert inventario["chaves_anteriores_com_fatos"] == 1
    assert inventario["chaves_anteriores_sem_fatos"] == 1
    assert inventario["primeiro_recebimento"] == "2025-03-30"
    assert inventario["ultimo_recebimento"] == "2025-05-01"
