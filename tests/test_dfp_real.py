"""Reconciliação opt-in da CLI com os registros do ZIP oficial de 2024."""

import csv
import hashlib
import os
import subprocess
from io import TextIOWrapper
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import pyarrow.parquet as pq
import pytest


def _conferir_membro(zip_dfp: ZipFile, membro: str, parquet: Path) -> int:
    with zip_dfp.open(membro) as arquivo, TextIOWrapper(
        arquivo, encoding="latin-1", newline=""
    ) as texto:
        leitor = csv.DictReader(texto, delimiter=";")
        colunas_csv = leitor.fieldnames
        csv_df = pd.DataFrame.from_records(leitor, columns=colunas_csv).astype("string")

    parquet_df = pd.read_parquet(
        parquet,
        columns=[*colunas_csv, "LINHA_ORIGEM"],
        filters=[("ARQUIVO_ORIGEM", "=", membro)],
    ).sort_values("LINHA_ORIGEM", ignore_index=True)
    assert len(parquet_df) == len(csv_df), membro
    assert parquet_df["LINHA_ORIGEM"].tolist() == list(range(1, len(csv_df) + 1)), membro

    for coluna in colunas_csv:
        esperado = csv_df[coluna].replace("", pd.NA)
        encontrado = parquet_df[coluna]
        if coluna.startswith("DT_"):
            encontrado = encontrado.dt.strftime("%Y-%m-%d")
        if coluna == "VERSAO":
            esperado = esperado.astype("Int64").astype("string")
        pd.testing.assert_series_equal(
            encontrado.astype("string"), esperado, obj=f"{membro}:{coluna}"
        )
    return len(csv_df)


def test_cli_dfp_2024_reconcilia_parquet_com_csv(tmp_path: Path) -> None:
    caminho_zip = os.environ.get("QUANTDISTRESS_TEST_DFP_2024")
    if not caminho_zip:
        pytest.skip("Defina QUANTDISTRESS_TEST_DFP_2024 com o caminho do ZIP oficial.")

    origem = Path(caminho_zip).resolve(strict=True)
    with origem.open("rb") as arquivo:
        sha256 = hashlib.file_digest(arquivo, "sha256").hexdigest()

    subprocess.run(
        [
            "quantdistress-dfp",
            "--ano", "2024",
            "--arquivo", str(origem),
            "--dados", str(tmp_path),
            "--sha256", sha256,
        ],
        check=True,
    )

    destino = tmp_path / "interim" / "dfp" / "2024" / sha256
    fatos = destino / "fatos.parquet"
    entregas = destino / "entregas.parquet"
    with ZipFile(origem) as zip_dfp:
        total_entregas = _conferir_membro(zip_dfp, "dfp_cia_aberta_2024.csv", entregas)
        total_fatos = sum(
            _conferir_membro(zip_dfp, f"dfp_cia_aberta_{familia}_{escopo}_2024.csv", fatos)
            for familia in ("BPA", "BPP", "DRE", "DFC_MD", "DFC_MI")
            for escopo in ("con", "ind")
        )

    assert pq.read_metadata(entregas).num_rows == total_entregas
    assert pq.read_metadata(fatos).num_rows == total_fatos
