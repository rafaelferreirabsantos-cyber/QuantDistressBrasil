"""Ingestão das demonstrações anuais da CVM e do índice de documentos DFP."""

import argparse
import csv
import re
from datetime import datetime, timezone
from io import TextIOWrapper
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile

import pandas as pd

from ._snapshot import adquirir_zip, gravar_json, ler_json, publicar, sha256

VERSAO_ESQUEMA = 1
FAMILIAS = ("BPA", "BPP", "DRE", "DFC_MD", "DFC_MI")
ESCOPO_DFP = {"con": "DF Consolidado", "ind": "DF Individual"}
CHAVE_ENTREGA = ("CNPJ_CIA", "CD_CVM", "DT_REFER", "VERSAO")
METADADOS_DOCUMENTO = ("ID_DOC", "DT_RECEB", "LINK_DOC")
CHAVE_FATO = (*CHAVE_ENTREGA, "ORDEM_EXERC", "DT_INI_EXERC", "DT_FIM_EXERC", "CD_CONTA")
COLUNAS_ENTREGA = (*CHAVE_ENTREGA, "DENOM_CIA", "CATEG_DOC", *METADADOS_DOCUMENTO)
COLUNAS_FATO = (
    *CHAVE_ENTREGA,
    "DENOM_CIA",
    "GRUPO_DFP",
    "MOEDA",
    "ESCALA_MOEDA",
    "ORDEM_EXERC",
    "DT_INI_EXERC",
    "DT_FIM_EXERC",
    "CD_CONTA",
    "DS_CONTA",
    "VL_CONTA",
    "ST_CONTA_FIXA",
)
COLUNAS_FATO_ADICIONAIS = (
    "FAMILIA",
    "ESCOPO",
    "ARQUIVO_ORIGEM",
    "LINHA_ORIGEM",
    "FATOR_ESCALA_MOEDA",
    "CHAVE_REPETIDA",
    "FATO_REPETIDO",
)
FATORES_ESCALA = {"UNIDADE": 1, "MIL": 1_000}


def _ler_csv(zip_dfp: ZipFile, membro: str, colunas: tuple[str, ...]) -> pd.DataFrame:
    with zip_dfp.open(membro) as bruto, TextIOWrapper(bruto, encoding="latin-1", newline="") as fluxo:
        registros = csv.reader(fluxo, delimiter=";", strict=True)
        cabecalho = next(registros, [])
        faltantes = sorted(set(colunas) - set(cabecalho))
        inesperadas = sorted(set(cabecalho) - set(colunas))
        if faltantes or inesperadas or len(cabecalho) != len(colunas):
            raise ValueError(
                f"{membro}: esquema divergente, cabeçalho={cabecalho}, "
                f"faltantes={faltantes}, inesperadas={inesperadas}."
            )
        linhas = []
        for numero, campos in enumerate(registros, start=1):
            if len(campos) != len(cabecalho):
                raise ValueError(f"{membro}: registro {numero} com {len(campos)} campos.")
            linhas.append(campos)

    quadro = pd.DataFrame(linhas, columns=cabecalho, dtype="string")[list(colunas)]
    return quadro.mask(quadro.eq(""))


def _converter_dias(quadro: pd.DataFrame, colunas: tuple[str, ...], membro: str) -> None:
    for coluna in colunas:
        if not quadro[coluna].str.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", na=True).all():
            raise ValueError(f"{membro}: formato inesperado em {coluna}.")
        try:
            quadro[coluna] = pd.to_datetime(quadro[coluna], format="%Y-%m-%d")
        except ValueError as erro:
            raise ValueError(f"{membro}: data inválida em {coluna}.") from erro


def _registrar_origem(quadro: pd.DataFrame, membro: str) -> None:
    if not quadro["VERSAO"].str.fullmatch(r"[0-9]+", na=True).all():
        raise ValueError(f"{membro}: formato inesperado em VERSAO.")
    quadro["VERSAO"] = quadro["VERSAO"].astype("Int64")
    quadro["ARQUIVO_ORIGEM"] = pd.Series(membro, index=quadro.index, dtype="string")
    quadro["LINHA_ORIGEM"] = quadro.index + 1


def _preparar_indice(entregas: pd.DataFrame, membro: str) -> pd.DataFrame:
    _converter_dias(entregas, ("DT_REFER", "DT_RECEB"), membro)
    _registrar_origem(entregas, membro)
    chave = list(CHAVE_ENTREGA)
    validas = entregas[chave].notna().all(axis=1)
    repetidas = validas & entregas.duplicated(chave, keep=False)
    entregas["CHAVE_ENTREGA_REPETIDA"] = repetidas
    vinculos = entregas.loc[validas, [*chave, *METADADOS_DOCUMENTO]].copy()
    vinculos["SITUACAO_VINCULO"] = pd.Series("unico", index=vinculos.index, dtype="string")
    vinculos.loc[repetidas, "SITUACAO_VINCULO"] = "ambiguo"
    vinculos.loc[repetidas, list(METADADOS_DOCUMENTO)] = pd.NA
    return vinculos.drop_duplicates(chave)


def _ler_fatos(
    zip_dfp: ZipFile, membro: str, familia: str, escopo: str, vinculos: pd.DataFrame
) -> pd.DataFrame:
    colunas = COLUNAS_FATO
    if familia in {"BPA", "BPP"}:
        colunas = tuple(coluna for coluna in colunas if coluna != "DT_INI_EXERC")
    fatos = _ler_csv(zip_dfp, membro, colunas)
    if not fatos["GRUPO_DFP"].str.startswith(ESCOPO_DFP[escopo] + " -", na=True).all():
        raise ValueError(f"{membro}: escopo no GRUPO_DFP divergente do nome do arquivo.")
    if not fatos["VL_CONTA"].str.fullmatch(r"[+-]?[0-9]+(?:\.[0-9]+)?", na=True).all():
        raise ValueError(f"{membro}: representação decimal inesperada em VL_CONTA.")
    fatos["FATO_REPETIDO"] = fatos.duplicated(keep=False)
    if "DT_INI_EXERC" not in fatos:
        fatos["DT_INI_EXERC"] = pd.Series(pd.NA, index=fatos.index, dtype="string")
    _converter_dias(fatos, ("DT_REFER", "DT_INI_EXERC", "DT_FIM_EXERC"), membro)
    _registrar_origem(fatos, membro)
    fatos["CHAVE_REPETIDA"] = fatos.duplicated(list(CHAVE_FATO), keep=False)
    fatos["FAMILIA"] = pd.Series(familia, index=fatos.index, dtype="string")
    fatos["ESCOPO"] = pd.Series(escopo, index=fatos.index, dtype="string")
    fatos["FATOR_ESCALA_MOEDA"] = fatos["ESCALA_MOEDA"].map(FATORES_ESCALA).astype("Int64")
    fatos = fatos[[*COLUNAS_FATO, *COLUNAS_FATO_ADICIONAIS]]
    fatos = fatos.merge(vinculos, how="left", on=list(CHAVE_ENTREGA), validate="many_to_one")
    fatos["SITUACAO_VINCULO"] = fatos["SITUACAO_VINCULO"].fillna("ausente")
    return fatos


def _processar_zip(arquivo: Path, ano: int, pasta: Path, fonte: dict) -> None:
    membro_indice = f"dfp_cia_aberta_{ano}.csv"
    membros_fatos = {
        f"dfp_cia_aberta_{familia}_{escopo}_{ano}.csv": (familia, escopo)
        for familia in FAMILIAS
        for escopo in ESCOPO_DFP
    }
    esperados = {membro_indice, *membros_fatos}
    with ZipFile(arquivo) as zip_dfp:
        nomes = zip_dfp.namelist()
        if len(nomes) != len(set(nomes)):
            raise ValueError(f"{arquivo.name}: nomes de membros ZIP duplicados.")
        faltantes = sorted(esperados - set(nomes))
        if faltantes:
            raise ValueError(f"{arquivo.name}: membros requeridos ausentes: {', '.join(faltantes)}.")
        entregas = _ler_csv(zip_dfp, membro_indice, COLUNAS_ENTREGA)
        vinculos = _preparar_indice(entregas, membro_indice)
        processados = [{"arquivo": membro_indice, "tipo": "entregas", "linhas": len(entregas)}]
        partes = []
        for membro, (familia, escopo) in membros_fatos.items():
            parte = _ler_fatos(zip_dfp, membro, familia, escopo, vinculos)
            partes.append(parte)
            processados.append(
                {
                    "arquivo": membro,
                    "tipo": "fatos",
                    "familia": familia,
                    "escopo": escopo,
                    "linhas": len(parte),
                }
            )
        fora_escopo = [
            {"arquivo": info.filename, "bytes_descompactados": info.file_size}
            for info in zip_dfp.infolist()
            if info.filename not in esperados
        ]

    partes_preenchidas = [parte for parte in partes if not parte.empty]
    fatos = pd.concat(partes_preenchidas, ignore_index=True) if partes_preenchidas else partes[0]
    tabelas = {}
    for nome, quadro in (("entregas", entregas), ("fatos", fatos)):
        destino = pasta / f"{nome}.parquet"
        quadro.to_parquet(destino, engine="pyarrow", index=False)
        tabelas[nome] = {"arquivo": destino.name, "linhas": len(quadro), "sha256": sha256(destino)}
    gravar_json(
        pasta / "manifesto.json",
        {
            "versao_esquema": VERSAO_ESQUEMA,
            "ano": ano,
            "fonte": fonte,
            "processado_em_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "membros_processados": processados,
            "membros_fora_escopo": fora_escopo,
            "tabelas": tabelas,
        },
    )


def ingerir_dfp(
    ano: int,
    dados: Path = Path("data"),
    *,
    arquivo: Path | None = None,
    sha256_esperado: str | None = None,
) -> Path:
    """Adquire o ZIP e devolve a pasta do snapshot com Parquets e manifesto."""
    if not 2010 <= ano <= 9999:
        raise ValueError("Informe um ano de quatro dígitos a partir de 2010.")
    if sha256_esperado is not None:
        if not re.fullmatch(r"[0-9a-fA-F]{64}", sha256_esperado):
            raise ValueError("O SHA-256 esperado deve ter 64 dígitos hexadecimais.")
        sha256_esperado = sha256_esperado.lower()
    raiz = dados.resolve()
    zip_local = adquirir_zip(ano, raiz / "raw" / "dfp" / str(ano), arquivo, sha256_esperado)
    fonte = ler_json(zip_local.parent / "origem.json")
    pasta_ano = raiz / "interim" / "dfp" / str(ano)
    destino = pasta_ano / fonte["sha256"]
    pasta_ano.mkdir(parents=True, exist_ok=True)
    if not destino.exists():
        with TemporaryDirectory(prefix=".processamento-", dir=pasta_ano) as temporario:
            entrada = Path(temporario)
            _processar_zip(zip_local, ano, entrada, fonte)
            publicar(entrada, destino)

    manifesto = ler_json(destino / "manifesto.json")
    if (manifesto["versao_esquema"], manifesto["ano"], manifesto["fonte"]["sha256"]) != (
        VERSAO_ESQUEMA, ano, fonte["sha256"]
    ):
        raise ValueError(f"Manifesto incompatível em {destino}.")
    for nome in ("entregas", "fatos"):
        parquet = destino / f"{nome}.parquet"
        if sha256(parquet) != manifesto["tabelas"][nome]["sha256"]:
            raise ValueError(f"Parquet local alterado após a ingestão: {parquet}")
    return destino


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingere um snapshot anual de DFP da CVM.")
    parser.add_argument("--ano", type=int, required=True, help="Ano de referência do pacote DFP.")
    parser.add_argument("--dados", type=Path, default=Path("data"), help="Diretório de dados.")
    parser.add_argument("--arquivo", type=Path, help="Importa um ZIP local.")
    parser.add_argument("--sha256", help="Verifica o hash SHA-256 contra este valor esperado.")
    args = parser.parse_args()
    try:
        destino = ingerir_dfp(args.ano, args.dados, arquivo=args.arquivo, sha256_esperado=args.sha256)
    except (ValueError, OSError, BadZipFile, csv.Error, KeyError) as erro:
        parser.exit(1, f"Falha na ingestão DFP {args.ano}: {erro}\n")
    print(destino)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
