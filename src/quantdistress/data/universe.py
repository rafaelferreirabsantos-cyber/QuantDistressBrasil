"""Universo documental DFP por exercício, com classificação cadastral da CVM."""

from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from .dfp import CHAVE_ENTREGA, ESCOPO_DFP

CHAVE_EMISSOR = ["CNPJ_CIA", "CD_CVM"]
CHAVE_REFERENCIA = [*CHAVE_EMISSOR, "DT_REFER"]
CHAVE_NORMALIZADA = ["CNPJ_COMPARACAO", "CVM_COMPARACAO"]
CHAVE_OBSERVACAO = [*CHAVE_ENTREGA, "ESCOPO"]
COLUNAS_FCA = {
    "CNPJ_Companhia": "CNPJ_CIA", "Codigo_CVM": "CD_CVM",
    "Data_Referencia": "DT_REFER_FCA", "Versao": "VERSAO_FCA", "ID_Documento": "ID_DOC_FCA",
    "Setor_Atividade": "SETOR_FCA", "Situacao_Registro_CVM": "SIT_REGISTRO_FCA",
    "Situacao_Emissor": "SIT_EMISSOR_FCA",
}
SETORES_FINANCEIROS = {"Bancos", "Intermediação Financeira", "Arrendamento Mercantil", "Crédito Imobiliário"}
SETORES_ESPECIFICOS = {
    "Bolsas de Valores/Mercadorias e Futuros", "Securitização de Recebíveis",
    "Seguradoras e Corretoras", "Sem Setor Principal",
}
SETORES_NAO_FINANCEIROS = {
    "Agricultura (Açúcar, Álcool e Cana)", "Alimentos", "Bebidas e Fumo", "Brinquedos e Lazer",
    "Comunicação e Informática", "Comércio (Atacado e Varejo)",
    "Construção Civil, Mat. Constr. e Decoração", "Const. Civil, Mat. Const. e Decoração",
    "Educação", "Embalagens", "Energia Elétrica", "Extração Mineral", "Farmacêutico e Higiene",
    "Gráficas e Editoras", "Hospedagem e Turismo", "Metalurgia e Siderurgia",
    "Máquinas, Equipamentos, Veículos e Peças", "Máqs., Equip., Veíc. e Peças",
    "Papel e Celulose", "Pesca", "Petroquímicos e Borracha", "Petróleo e Gás", "Reflorestamento",
    "Saneamento, Serv. Água e Gás", "Serviços Transporte e Logística", "Serviços médicos",
    "Telecomunicações", "Têxtil e Vestuário",
}
CLASSIFICACAO = {
    **dict.fromkeys(SETORES_FINANCEIROS, "financeira"),
    **dict.fromkeys(SETORES_ESPECIFICOS, "regime_especifico"),
    **dict.fromkeys(SETORES_NAO_FINANCEIROS, "nao_financeira"),
}


def _identificadores(tabela: pd.DataFrame) -> pd.DataFrame:
    cnpj = tabela["CNPJ_CIA"].astype("string").str.strip().str.replace(r"[./-]", "", regex=True)
    codigo = tabela["CD_CVM"].astype("string").str.strip()
    return tabela.assign(
        CNPJ_COMPARACAO=cnpj.where(cnpj.str.fullmatch(r"[0-9]{14}", na=False)),
        CVM_COMPARACAO=codigo.where(codigo.str.fullmatch(r"[0-9]{1,6}", na=False)).str.zfill(6),
    )


def _ler_colunas(entrada, colunas) -> pd.DataFrame:
    return pd.read_csv(
        entrada, sep=";", encoding="latin-1", dtype="string", usecols=list(colunas),
        keep_default_na=False, na_values=[""],
    )


def ler_fca(arquivo: Path, ano: int) -> pd.DataFrame:
    """Extrai a seção geral e a vincula ao índice por documento, emissor, data e versão."""
    membro = f"fca_cia_aberta_geral_{ano}.csv"
    campos_indice = {
        "ID_DOC": "ID_DOC_FCA", "DT_REFER": "DT_REFER_FCA", "VERSAO": "VERSAO_FCA",
        "DT_RECEB": "DT_RECEB_FCA", "CNPJ_CIA": "CNPJ_CIA", "CD_CVM": "CD_CVM",
    }
    with ZipFile(arquivo) as pacote:
        with pacote.open(membro) as entrada:
            geral = _ler_colunas(entrada, COLUNAS_FCA).rename(columns=COLUNAS_FCA)
        with pacote.open(f"fca_cia_aberta_{ano}.csv") as entrada:
            indice = _ler_colunas(entrada, campos_indice).rename(columns=campos_indice)
    chave = [*CHAVE_NORMALIZADA, "DT_REFER_FCA", "VERSAO_FCA", "ID_DOC_FCA"]
    geral = _identificadores(geral).assign(ARQUIVO_ORIGEM_FCA=membro, LINHA_ORIGEM_FCA=geral.index + 1)
    indice = _identificadores(indice)[[*chave, "DT_RECEB_FCA"]].dropna(subset=chave)
    # Uma data só é atribuída quando o índice apresenta vínculo inequívoco.
    indice = indice.loc[~indice.duplicated(chave, keep=False)]
    geral = geral.merge(indice, on=chave, how="left", validate="many_to_one")
    for coluna in ("DT_REFER_FCA", "DT_RECEB_FCA"):
        geral[coluna] = pd.to_datetime(geral[coluna], format="%Y-%m-%d")
    geral["VERSAO_FCA"] = geral["VERSAO_FCA"].astype("Int64")
    return geral


def ler_cadastro_atual(arquivo: Path) -> pd.DataFrame:
    """Carrega somente os campos úteis ao diagnóstico de cancelamento posterior."""
    cadastro = _identificadores(_ler_colunas(arquivo, [*CHAVE_EMISSOR, "SIT", "DT_CANCEL"]))
    cadastro = cadastro[[*CHAVE_NORMALIZADA, "SIT", "DT_CANCEL"]].dropna(subset=CHAVE_NORMALIZADA)
    cadastro = cadastro.rename(columns={"SIT": "SIT_CAD_COLETA", "DT_CANCEL": "DT_CANCEL_CAD"})
    cadastro["DT_CANCEL_CAD"] = pd.to_datetime(cadastro["DT_CANCEL_CAD"], format="%Y-%m-%d")
    return cadastro.drop_duplicates()


def _classificar_fca(observacoes: pd.DataFrame, fca: pd.DataFrame) -> pd.DataFrame:
    validas = fca.dropna(subset=[*CHAVE_NORMALIZADA, "DT_REFER_FCA", "VERSAO_FCA", "ID_DOC_FCA"])
    candidatas = observacoes[CHAVE_REFERENCIA + CHAVE_NORMALIZADA].merge(
        validas.drop(columns=CHAVE_EMISSOR), on=CHAVE_NORMALIZADA, how="inner",
    )
    candidatas = candidatas.loc[
        candidatas["DT_REFER_FCA"].le(candidatas["DT_REFER"])
        & candidatas["DT_REFER_FCA"].dt.year.eq(candidatas["DT_REFER"].dt.year)
    ]
    for coluna in ("DT_REFER_FCA", "VERSAO_FCA"):
        maior = candidatas.groupby(CHAVE_REFERENCIA)[coluna].transform("max")
        candidatas = candidatas.loc[candidatas[coluna].eq(maior)]
    ambiguas = candidatas.loc[candidatas.duplicated(CHAVE_REFERENCIA, keep=False), CHAVE_REFERENCIA]
    escolhidas = candidatas.loc[~candidatas.duplicated(CHAVE_REFERENCIA, keep=False)]
    resultado = observacoes.merge(
        escolhidas.drop(columns=CHAVE_NORMALIZADA), on=CHAVE_REFERENCIA, how="left", validate="one_to_one",
    )
    ambiguas = pd.MultiIndex.from_frame(ambiguas)
    resultado["VINCULO_FCA"] = "ausente"
    resultado.loc[resultado["ID_DOC_FCA"].notna(), "VINCULO_FCA"] = "unico"
    resultado.loc[pd.MultiIndex.from_frame(resultado[CHAVE_REFERENCIA]).isin(ambiguas), "VINCULO_FCA"] = "ambiguo"
    setor = resultado["SETOR_FCA"].str.strip().str.removeprefix("Emp. Adm. Part. - ")
    resultado["GRUPO_SETORIAL"] = setor.map(CLASSIFICACAO).fillna("nao_classificada")
    resultado["FCA_RECEBIDA_APOS_REFERENCIA"] = (
        resultado["DT_RECEB_FCA"].gt(resultado["DT_REFER"]).where(resultado["DT_RECEB_FCA"].notna()).astype("boolean")
    )
    return resultado


def _anexar_cadastro(observacoes: pd.DataFrame, cadastro: pd.DataFrame) -> pd.DataFrame:
    repetidas = cadastro.duplicated(CHAVE_NORMALIZADA, keep=False)
    ambiguas = pd.MultiIndex.from_frame(cadastro.loc[repetidas, CHAVE_NORMALIZADA])
    resultado = observacoes.merge(
        cadastro.loc[~repetidas], on=CHAVE_NORMALIZADA, how="left", validate="many_to_one",
    )
    resultado["VINCULO_CAD_COLETA"] = "ausente"
    presente = resultado[["SIT_CAD_COLETA", "DT_CANCEL_CAD"]].notna().any(axis=1)
    resultado.loc[presente, "VINCULO_CAD_COLETA"] = "unico"
    resultado.loc[pd.MultiIndex.from_frame(resultado[CHAVE_NORMALIZADA]).isin(ambiguas), "VINCULO_CAD_COLETA"] = "ambiguo"
    resultado["CANCELAMENTO_POSTERIOR"] = (
        resultado["DT_CANCEL_CAD"].gt(resultado["DT_REFER"])
        .where(resultado["DT_CANCEL_CAD"].notna()).astype("boolean")
    )
    return resultado.drop(columns=CHAVE_NORMALIZADA)


def construir_universo(
    entregas: pd.DataFrame, fca: pd.DataFrame, cadastro: pd.DataFrame,
) -> pd.DataFrame:
    """Mantém referências do índice por escopo, inclusive sem fatos ou classe setorial."""
    base = _identificadores(entregas).dropna(subset=[*CHAVE_REFERENCIA, *CHAVE_NORMALIZADA])
    maximas = base.groupby(CHAVE_REFERENCIA)["VERSAO"].transform("max")
    atuais = base.loc[base["VERSAO"].eq(maximas).fillna(False)]
    contagem = atuais.groupby(CHAVE_REFERENCIA)["VERSAO"].agg(
        VERSAO="max", N_ENTREGAS_VERSAO_MAXIMA="size",
    ).reset_index()
    colunas_versao = [*CHAVE_REFERENCIA, "DT_RECEB", "ID_DOC", "LINK_DOC"]
    unicas = atuais.loc[~atuais.duplicated(CHAVE_REFERENCIA, keep=False), colunas_versao]
    observacoes = base[[*CHAVE_REFERENCIA, *CHAVE_NORMALIZADA]].drop_duplicates()
    observacoes = observacoes.merge(contagem, on=CHAVE_REFERENCIA, how="left", validate="one_to_one")
    observacoes = observacoes.merge(unicas, on=CHAVE_REFERENCIA, how="left", validate="one_to_one")
    observacoes["N_ENTREGAS_VERSAO_MAXIMA"] = observacoes["N_ENTREGAS_VERSAO_MAXIMA"].fillna(0).astype("Int64")
    observacoes["SITUACAO_ENTREGA_DFP"] = observacoes["N_ENTREGAS_VERSAO_MAXIMA"].map(
        {0: "versao_ausente", 1: "unica"}
    ).fillna("ambigua")
    observacoes = _classificar_fca(observacoes, fca)
    observacoes = _anexar_cadastro(observacoes, cadastro)
    observacoes["DT_DIVULGACAO"] = pd.NaT
    observacoes["MODO_TEMPORAL"] = "descritivo_revisado"
    return observacoes.merge(pd.DataFrame({"ESCOPO": list(ESCOPO_DFP)}), how="cross")
