"""Aquisição e publicação de snapshots identificados pelo conteúdo."""

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import Request, urlopen
from zipfile import is_zipfile


def sha256(arquivo: Path) -> str:
    with arquivo.open("rb") as fluxo:
        return hashlib.file_digest(fluxo, "sha256").hexdigest()


def gravar_json(arquivo: Path, dados: dict) -> None:
    arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ler_json(arquivo: Path) -> dict:
    return json.loads(arquivo.read_text(encoding="utf-8"))


def publicar(pasta_temporaria: Path, destino: Path) -> None:
    """Disponibiliza uma pasta inteira, mantendo qualquer publicação concorrente."""
    try:
        pasta_temporaria.rename(destino)
    except OSError:
        if not destino.is_dir():
            raise


def adquirir_zip(
    ano: int, pasta_raw: Path, arquivo: Path | None, sha256_esperado: str | None
) -> Path:
    nome_zip = f"dfp_cia_aberta_{ano}.zip"
    url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/{nome_zip}"
    pasta_raw.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".recebimento-", dir=pasta_raw) as temporario:
        entrada = Path(temporario)
        zip_temporario = entrada / nome_zip
        metadados = {"arquivo_zip": nome_zip, "url_oficial": url}
        if arquivo is None:
            pedido = Request(url, headers={"User-Agent": "QuantDistressBrasil/0.1"})
            with urlopen(pedido, timeout=60) as resposta, zip_temporario.open("wb") as saida:
                shutil.copyfileobj(resposta, saida)
                metadados.update(
                    origem="cvm",
                    url_efetiva=resposta.geturl(),
                    http_last_modified=resposta.headers.get("Last-Modified"),
                    http_etag=resposta.headers.get("ETag"),
                )
        else:
            shutil.copyfile(arquivo, zip_temporario)
            metadados.update(origem="arquivo_local", arquivo_importado=arquivo.name)

        resumo = sha256(zip_temporario)
        if sha256_esperado is not None and sha256_esperado != resumo:
            raise ValueError(f"SHA-256 divergente (esperado {sha256_esperado}, recebido {resumo}).")
        if not is_zipfile(zip_temporario):
            raise ValueError(f"A origem de {nome_zip} não entregou um ZIP válido.")
        metadados.update(
            sha256=resumo,
            bytes_zip=zip_temporario.stat().st_size,
            capturado_em_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        gravar_json(entrada / "origem.json", metadados)
        pasta_snapshot = pasta_raw / resumo
        publicar(entrada, pasta_snapshot)

    arquivo_snapshot = pasta_snapshot / nome_zip
    if sha256(arquivo_snapshot) != resumo:
        raise ValueError(f"ZIP local alterado após a aquisição: {arquivo_snapshot}")
    if ler_json(pasta_snapshot / "origem.json")["sha256"] != resumo:
        raise ValueError(f"Proveniência inconsistente em {pasta_snapshot}.")
    return arquivo_snapshot
