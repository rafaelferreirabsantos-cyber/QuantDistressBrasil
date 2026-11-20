"""Testes de integridade com um ZIP pequeno construído para os testes."""

import csv
import hashlib
import io
import json
from zipfile import ZipFile

import pandas as pd
import pytest

from quantdistress.data.dfp import (
    COLUNAS_ENTREGA,
    COLUNAS_FATO,
    ESCOPO_DFP,
    FAMILIAS,
    ingerir_dfp,
)

ANO = 2024
INDICE = "dfp_cia_aberta_2024.csv"
BPA_CON = "dfp_cia_aberta_BPA_con_2024.csv"


def _csv(colunas, registros):
    destino = io.StringIO(newline="")
    escritor = csv.DictWriter(destino, colunas, delimiter=";")
    escritor.writeheader()
    escritor.writerows(registros)
    return destino.getvalue().encode("latin-1")


def _criar_zip(arquivo, *, omitir=None):
    companhia = {
        "CNPJ_CIA": "00.000.000/0001-91",
        "CD_CVM": "001023",
        "DT_REFER": "2024-09-30",
        "DENOM_CIA": "Companhia de Teste",
    }
    indice = {**companhia, "CATEG_DOC": "DFP", "LINK_DOC": "https://example.invalid/dfp"}
    entregas = [
        dict(indice, VERSAO="1", ID_DOC="00001", DT_RECEB="2024-10-15"),
        dict(indice, VERSAO="2", ID_DOC="00002", DT_RECEB="2024-10-20"),
        dict(indice, VERSAO="2", ID_DOC="00003", DT_RECEB="2024-11-20"),
        dict(indice, VERSAO="", ID_DOC="00004", DT_RECEB="2024-11-21"),
    ]
    fato = {
        **companhia,
        "VERSAO": "1",
        "GRUPO_DFP": "DF Consolidado - Balanço Patrimonial Ativo",
        "MOEDA": "REAL",
        "ESCALA_MOEDA": "MIL",
        "ORDEM_EXERC": "ÚLTIMO",
        "DT_FIM_EXERC": "2024-09-30",
        "CD_CONTA": "1",
        "DS_CONTA": 'Ativo total; descrição "original"',
        "VL_CONTA": "1234.0000000001",
        "ST_CONTA_FIXA": "S",
    }

    with ZipFile(arquivo, "w") as zip_dfp:
        zip_dfp.writestr(INDICE, _csv(COLUNAS_ENTREGA, entregas))
        zip_dfp.writestr("dfp_cia_aberta_DMPL_con_2024.csv", "inventario")
        for familia in FAMILIAS:
            for escopo in ESCOPO_DFP:
                membro = f"dfp_cia_aberta_{familia}_{escopo}_{ANO}.csv"
                if membro == omitir:
                    continue
                colunas = COLUNAS_FATO
                if familia in {"BPA", "BPP"}:
                    colunas = tuple(campo for campo in colunas if campo != "DT_INI_EXERC")
                registros = []
                if membro == BPA_CON:
                    registros = [
                        fato,
                        fato.copy(),
                        dict(fato, VL_CONTA="1234.0000000002"),
                        dict(fato, ORDEM_EXERC="PENÚLTIMO", DT_FIM_EXERC="2023-09-30"),
                        dict(fato, VERSAO="2", ESCALA_MOEDA="UNIDADE"),
                        dict(fato, VERSAO="3", ESCALA_MOEDA="DESCONHECIDA"),
                        dict(fato, VERSAO="", VL_CONTA=""),
                    ]
                elif familia == "DRE" and escopo == "ind":
                    registros = [
                        dict(fato, GRUPO_DFP="DF Individual - Demonstração do Resultado",
                             DT_INI_EXERC="2024-01-01", CD_CONTA="3.01")
                    ]
                zip_dfp.writestr(membro, _csv(colunas, registros))


def test_preserva_linhas_e_vincula_apenas_entregas_inequivocas(tmp_path):
    arquivo = tmp_path / "entrada.zip"
    _criar_zip(arquivo)
    esperado = hashlib.sha256(arquivo.read_bytes()).hexdigest()
    dados = tmp_path / "data"
    pasta = ingerir_dfp(ANO, dados, arquivo=arquivo, sha256_esperado=esperado.upper())

    assert pasta == dados / "interim" / "dfp" / str(ANO) / esperado
    manifesto = json.loads((pasta / "manifesto.json").read_text(encoding="utf-8"))
    fonte = manifesto["fonte"]
    assert fonte["origem"] == "arquivo_local"
    assert fonte["sha256"] == esperado
    assert fonte["bytes_zip"] == arquivo.stat().st_size
    assert len(manifesto["membros_processados"]) == 11
    assert len(manifesto["membros_fora_escopo"]) == 1
    assert manifesto["tabelas"]["fatos"]["linhas"] == 8
    assert manifesto["tabelas"]["entregas"]["linhas"] == 4

    fatos = pd.read_parquet(pasta / "fatos.parquet")
    entregas = pd.read_parquet(pasta / "entregas.parquet")
    assert entregas["CHAVE_ENTREGA_REPETIDA"].tolist() == [False, True, True, False]
    assert len(fatos) == 8
    bpa = fatos[fatos["FAMILIA"].eq("BPA")]
    assert bpa["ESCOPO"].eq("con").all()
    assert bpa["CNPJ_CIA"].eq("00.000.000/0001-91").all()
    assert bpa["CD_CVM"].eq("001023").all()
    assert bpa["DS_CONTA"].eq('Ativo total; descrição "original"').all()
    assert bpa["ARQUIVO_ORIGEM"].eq(BPA_CON).all()
    assert bpa["LINHA_ORIGEM"].tolist() == list(range(1, 8))
    assert bpa["VL_CONTA"].iloc[0] == "1234.0000000001"
    assert bpa["CHAVE_REPETIDA"].tolist() == [True, True, True, False, False, False, False]
    assert bpa["FATO_REPETIDO"].tolist() == [True, True, False, False, False, False, False]
    assert bpa["SITUACAO_VINCULO"].tolist() == ["unico"] * 4 + ["ambiguo", "ausente", "ausente"]
    assert bpa.iloc[0]["ID_DOC"] == "00001"
    assert bpa.iloc[0]["DT_RECEB"] == pd.Timestamp("2024-10-15")
    assert bpa.iloc[3]["DT_FIM_EXERC"] == pd.Timestamp("2023-09-30")
    assert bpa.iloc[4]["FATOR_ESCALA_MOEDA"] == 1
    assert pd.isna(bpa.iloc[5]["FATOR_ESCALA_MOEDA"])
    assert pd.isna(bpa.iloc[6]["VL_CONTA"])
    assert bpa.iloc[4:][["ID_DOC", "DT_RECEB", "LINK_DOC"]].isna().all().all()
    assert bpa["DT_INI_EXERC"].isna().all()
    assert fatos.iloc[-1]["DT_INI_EXERC"] == pd.Timestamp("2024-01-01")
    assert fatos.iloc[-1]["ESCOPO"] == "ind"


def test_reexecucao_preserva_snapshot_e_rejeita_parquet_alterado(tmp_path):
    arquivo = tmp_path / "entrada.zip"
    _criar_zip(arquivo)
    dados = tmp_path / "data"
    pasta = ingerir_dfp(ANO, dados, arquivo=arquivo)
    manifesto = pasta / "manifesto.json"
    publicado_em = manifesto.stat().st_mtime_ns
    assert ingerir_dfp(ANO, dados, arquivo=arquivo) == pasta
    assert manifesto.stat().st_mtime_ns == publicado_em

    with (pasta / "fatos.parquet").open("ab") as saida:
        saida.write(b"alteracao")
    with pytest.raises(ValueError, match="Parquet local alterado"):
        ingerir_dfp(ANO, dados, arquivo=arquivo)


def test_hash_incorreto_nao_publica_snapshot(tmp_path):
    arquivo = tmp_path / "entrada.zip"
    _criar_zip(arquivo)
    dados = tmp_path / "data"
    with pytest.raises(ValueError, match="SHA-256 divergente"):
        ingerir_dfp(ANO, dados, arquivo=arquivo, sha256_esperado="0" * 64)
    assert not list((dados / "raw" / "dfp" / str(ANO)).iterdir())
    assert not (dados / "interim").exists()


def test_membro_ausente_nao_publica_resultado_parcial(tmp_path):
    arquivo = tmp_path / "entrada.zip"
    _criar_zip(arquivo, omitir=BPA_CON)
    dados = tmp_path / "data"
    with pytest.raises(ValueError, match=f"membros requeridos ausentes: {BPA_CON}"):
        ingerir_dfp(ANO, dados, arquivo=arquivo)
    assert not list((dados / "interim" / "dfp" / str(ANO)).iterdir())
