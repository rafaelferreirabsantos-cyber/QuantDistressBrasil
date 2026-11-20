import pandas as pd
import pytest

from quantdistress.data._snapshot import gravar_json, sha256
from quantdistress.evaluation.panel import _abrir_snapshot


def test_snapshot_exige_escolha_explicita_e_verifica_parquet(tmp_path):
    hashes = ("a" * 64, "b" * 64)
    quadro = pd.DataFrame({"CD_CVM": ["000001"]})
    for digest in hashes:
        pasta = tmp_path / "interim" / "dfp" / "2024" / digest
        pasta.mkdir(parents=True)
        tabelas = {}
        for nome in ("entregas", "fatos"):
            caminho = pasta / f"{nome}.parquet"
            quadro.to_parquet(caminho)
            tabelas[nome] = {"sha256": sha256(caminho), "linhas": len(quadro)}
        gravar_json(pasta / "manifesto.json", {"ano": 2024, "fonte": {"sha256": digest}, "tabelas": tabelas})

    with pytest.raises(ValueError, match="Use --snapshot"):
        _abrir_snapshot(tmp_path, 2024, None)
    fonte, entregas, fatos = _abrir_snapshot(tmp_path, 2024, hashes[1])
    assert fonte["sha256"] == hashes[1]
    pd.testing.assert_frame_equal(entregas, quadro)
    pd.testing.assert_frame_equal(fatos, quadro)

    (pasta / "fatos.parquet").write_bytes(b"arquivo alterado no teste")
    with pytest.raises(ValueError, match="Hash divergente"):
        _abrir_snapshot(tmp_path, 2024, hashes[1])
