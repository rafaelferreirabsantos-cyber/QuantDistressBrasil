"""Calcula os dois eixos experimentais no painel descritivo revisado da CVM."""

import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

import numpy as np
import pandas as pd

from quantdistress.data._snapshot import ler_json
from quantdistress.data.universe import CHAVE_REFERENCIA
from quantdistress.evaluation.feasibility03 import PRESSAO, _referencias_consolidadas
from quantdistress.evaluation.normalization03 import _normalizar
from quantdistress.evaluation.references03 import AmostraReferencia, agrupar_referencias, percentil_ponto_medio
from quantdistress.evaluation.revision03 import ROTULO_MACRO, diagnostico_contabil
from quantdistress.features.indicators import PROTOTIPOS

from .configuration import COMPONENTES, MODO_TEMPORAL, VERSAO_METODOLOGICA, Scenario, hash_canonico


UNIDADE = ["ANO_ARQUIVO", "CD_CVM", "ESCOPO"]
DOCUMENTO = [*UNIDADE, "DT_REFER", "CNPJ_CIA", "VERSAO", "ID_DOC"]
COLUNAS_INDICADOR = ["INDICADOR", "VALOR", "SITUACAO", "DETALHE", "FONTES"]
METADADOS = [
    *DOCUMENTO, "SETOR_FCA", "GRUPO_SETORIAL", "VINCULO_FCA", "SITUACAO_ENTREGA_DFP", "LINK_DOC",
    "DT_RECEB", "DT_DIVULGACAO", "DT_COLETA_DFP", "SHA256_DFP", "MODO_TEMPORAL", "ID_DOC_FCA",
    "VERSAO_FCA", "ARQUIVO_ORIGEM_FCA", "LINHA_ORIGEM_FCA", "DT_REFER_FCA", "DT_RECEB_FCA",
    "FCA_RECEBIDA_APOS_REFERENCIA", "N_FATOS_CORRENTES_SELECIONADOS", "N_ENTREGAS_VERSAO_MAXIMA",
    "SIT_CAD_COLETA", "DT_CANCEL_CAD", "CANCELAMENTO_POSTERIOR",
]
METADADOS_FONTE = ["CONSOLIDADO_NA_FONTE", "URL_OFICIAL_DFP", "SHA256_FCA", "URL_OFICIAL_FCA"]
LINHAGEM_OK = "linhagem_validada_automaticamente"
CHAVE_EXATA = ["ANO_ARQUIVO", "ESCOPO", "COMPONENTE", "SETOR_FCA"]
CHAVE_MACRO = ["ANO_ARQUIVO", "ESCOPO", "COMPONENTE", "MACROSETOR"]


def load_panel(panel: Path, dados: Path = Path("data")) -> pd.DataFrame:
    """Carrega as partições do manifesto e verifica a presença de consolidado na fonte."""
    manifesto = ler_json(panel / "manifesto.json")
    anos = manifesto["anos"]
    if manifesto["modo_temporal"] != MODO_TEMPORAL or not anos or len({r["ano"] for r in anos}) != len(anos):
        raise ValueError("Esperado um painel descritivo revisado com partições anuais distintas.")
    particoes = []
    for info in anos:
        ano = info["ano"]
        fonte = info["fonte_dfp"]
        tabela = pd.read_parquet(panel / str(ano) / "indicadores.parquet", columns=[*METADADOS, *COLUNAS_INDICADOR])
        ano_fiscal = tabela["DT_REFER"].dt.year
        correta = (
            tabela["ANO_ARQUIVO"].eq(ano) & (ano_fiscal.isna() | ano_fiscal.eq(ano))
            & tabela["MODO_TEMPORAL"].eq(MODO_TEMPORAL) & tabela["SHA256_DFP"].eq(fonte["sha256"])
        )
        if len(tabela) != info["observacoes_indicadores"] or not correta.fillna(False).all():
            raise ValueError(f"Partição incompatível com o manifesto: {ano}.")
        snapshot = dados / "interim" / "dfp" / str(ano) / fonte["sha256"]
        if all((snapshot / arquivo).is_file() for arquivo in ("manifesto.json", "fatos.parquet")):
            indice = ler_json(snapshot / "manifesto.json")
            if indice["ano"] != ano or indice["fonte"]["sha256"] != fonte["sha256"]:
                raise ValueError(f"Manifesto da fonte DFP incompatível com o painel: {ano}.")
            tabela = tabela.merge(_referencias_consolidadas(snapshot), how="left", on=CHAVE_REFERENCIA, validate="many_to_one")
            tabela["CONSOLIDADO_NA_FONTE"] = tabela["CONSOLIDADO_NA_FONTE"].eq(True).astype("boolean")
        else:
            tabela["CONSOLIDADO_NA_FONTE"] = pd.Series(pd.NA, index=tabela.index, dtype="boolean")
        particoes.append(tabela.assign(URL_OFICIAL_DFP=fonte["url_oficial"], SHA256_FCA=info["sha256_fca"], URL_OFICIAL_FCA=info["url_fca"]))
    return pd.concat(particoes, ignore_index=True)


def _selecionar_documentos(painel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    metadados = [*METADADOS, *METADADOS_FONTE]
    observacoes = painel[metadados].drop_duplicates()
    ultimo = observacoes.groupby(UNIDADE)["DT_REFER"].transform("max")
    candidatas = observacoes.loc[observacoes["DT_REFER"].eq(ultimo) | ultimo.isna()].copy()
    ambiguas = candidatas.duplicated(UNIDADE, keep=False)
    candidatas["N_DOCUMENTOS_CANDIDATOS"] = 1
    candidatas["DOCUMENTOS_CANDIDATOS"] = None
    unicas = candidatas.loc[~ambiguas].copy()
    bloqueadas = []
    for _, grupo in candidatas.loc[ambiguas].groupby(UNIDADE, sort=False):
        registro = {coluna: grupo[coluna].iloc[0] if grupo[coluna].nunique(dropna=False) == 1 else None for coluna in metadados}
        candidatos = grupo[["CNPJ_CIA", "DT_REFER", "VERSAO", "ID_DOC", "SHA256_DFP"]].sort_values(
            ["CNPJ_CIA", "DT_REFER", "VERSAO", "ID_DOC"], na_position="last",
        )
        registro.update(N_DOCUMENTOS_CANDIDATOS=len(grupo), DOCUMENTOS_CANDIDATOS=candidatos.to_json(orient="records", date_format="iso"))
        bloqueadas.append(registro)
    selecionadas = pd.concat([unicas, pd.DataFrame(bloqueadas)], ignore_index=True).sort_values(UNIDADE).reset_index(drop=True)
    selecionadas["OBS_ID"] = selecionadas.index
    chaves = selecionadas.loc[selecionadas["N_DOCUMENTOS_CANDIDATOS"].eq(1), [*DOCUMENTO, "OBS_ID"]]
    razoes = chaves.merge(painel[[*DOCUMENTO, *COLUNAS_INDICADOR]], on=DOCUMENTO, how="inner", validate="one_to_many")
    repetidas = razoes.duplicated(["OBS_ID", "INDICADOR"], keep=False)
    if repetidas.any():
        bloqueios = razoes.loc[repetidas, ["OBS_ID", "INDICADOR"]].drop_duplicates().assign(SITUACAO="indicador_ambiguo")
        razoes = pd.concat([razoes.loc[~repetidas], bloqueios], ignore_index=True)
    return selecionadas, razoes


def _elegibilidade(observacoes: pd.DataFrame, scenario: Scenario) -> pd.Series:
    holding = observacoes["SETOR_FCA"].str.startswith("Emp. Adm. Part. - ", na=False)
    individual = observacoes["ESCOPO"].eq("ind")
    criterios = [
        (observacoes["DT_REFER"].isna(), "referencia_ausente"),
        (observacoes["N_DOCUMENTOS_CANDIDATOS"].gt(1) | observacoes["SITUACAO_ENTREGA_DFP"].eq("ambigua"), "documento_ambiguo"),
        (~observacoes["SITUACAO_ENTREGA_DFP"].eq("unica") | observacoes["ID_DOC"].isna(), "documento_indisponivel"),
        (~observacoes["VINCULO_FCA"].eq("unico") | observacoes["SETOR_FCA"].isna(), "setor_sem_evidencia"),
        (~observacoes["GRUPO_SETORIAL"].eq("nao_financeira"), "setor_nao_elegivel"),
        (individual & holding, "holding_individual"),
        (holding & (not scenario.holdings), "holding_excluida"),
        (individual & observacoes["CONSOLIDADO_NA_FONTE"].isna(), "consolidado_sem_evidencia"),
        (individual & observacoes["CONSOLIDADO_NA_FONTE"].eq(True), "consolidado_presente_na_fonte"),
    ]
    masks, motivos = zip(*criterios, strict=True)
    return pd.Series(np.select([mask.to_numpy(dtype=bool, na_value=False) for mask in masks], motivos, default="elegivel"), index=observacoes.index)


def _marcador_caixa(fontes: str, documento: str) -> str:
    try:
        contas = {f["CONCEITO"]: Decimal(f["VL_CONTA"]) for f in json.loads(fontes) if f["ID_DOC"] == documento}
        caixa = contas["caixa_equivalentes"]
        if caixa > 0:
            return "caixa_positivo"
        if caixa == 0:
            financiamentos = contas.get("financiamentos_circulantes")
            if financiamentos is None:
                return "caixa_zero_financiamento_ausente"
            return "caixa_zero_com_financiamento" if financiamentos > 0 else "caixa_zero_sem_financiamento_reportado"
    except (TypeError, ValueError, KeyError, InvalidOperation):
        pass
    return "caixa_nao_verificado"


class _Pares:
    """Coorte ordenada por código, com seleção determinística para choques."""

    def __init__(self, serie: pd.Series, chave: tuple, scenario: Scenario):
        self.serie = serie.sort_index()
        self.chave = chave
        self.amostra = AmostraReferencia(self.serie)
        self.min_pares = scenario.min_peers
        self.composition = scenario.composition
        self.ordem_choque = sorted(self.serie.index, key=lambda cvm: hashlib.sha256(
            f"{scenario.composition}|{chave!r}|{cvm}".encode("utf-8")
        ).digest()) if scenario.composition != "original" else []

    def preparar(self, cvm: str):
        codigos = self.serie.index[self.serie.index != cvm]
        if self.composition == "original":
            ref = self.amostra.preparar(min_pares=self.min_pares, emissor_excluido=cvm)
            return ref, codigos
        n_excluir = len(codigos) // 5
        ordem = [codigo for codigo in self.ordem_choque if codigo != cvm]
        mantidos = codigos.difference(ordem[:n_excluir], sort=False)
        ref = AmostraReferencia(self.serie.loc[mantidos]).preparar(min_pares=self.min_pares)
        return ref, mantidos


def _referencia(cvm, valor, pares, metodo: str) -> dict:
    if pares is None:
        return {
            "S_ESTATISTICO": "sem_referencia", "N_PARES": 0, "PONTOS": np.nan,
            "N_VALORES_DISTINTOS": 0, "MAIOR_EMPATE": 0, "MAIOR_MASSA_EMPATE": np.nan,
            "REF_MIN": np.nan, "REF_MAX": np.nan, "REF_IQR": np.nan,
            "CODIGOS_PARES_SHA256": None, "REFERENCIA_SHA256": None,
        }
    ref, codigos = pares.preparar(cvm)
    n = ref.n_pares
    pontos = np.nan
    status = ref.situacao
    if n:
        q1, q3 = np.quantile(ref.valores, [.25, .75])
    if status == "utilizavel":
        if metodo == "percentil":
            pontos = percentil_ponto_medio(valor, ref)
        else:
            # O teste da escala robusta independe de o alvo ter um valor disponível.
            probe = valor if np.isfinite(valor) else ref.valores[0]
            normalizado = _normalizar(np.array([probe]), ref.valores, metodo, pares.min_pares)[0]
            if np.isnan(normalizado):
                status = "escala_robusta_nula"
            elif np.isfinite(valor):
                pontos = normalizado
    return {
        "S_ESTATISTICO": status, "N_PARES": n, "PONTOS": pontos,
        "N_VALORES_DISTINTOS": len(np.unique(ref.valores)), "MAIOR_EMPATE": ref.maior_empate,
        "MAIOR_MASSA_EMPATE": ref.maior_empate / n if n else np.nan,
        "REF_MIN": ref.valores.min() if n else np.nan,
        "REF_MAX": ref.valores.max() if n else np.nan,
        "REF_IQR": q3 - q1 if n else np.nan,
        "CODIGOS_PARES_SHA256": hash_canonico(list(codigos)) if n else None,
        "REFERENCIA_SHA256": hash_canonico([(c, float(v).hex()) for c, v in zip(codigos, ref.valores, strict=True)]) if n else None,
    }


def _calcular_componentes(observacoes, razoes, scenario, config_id) -> pd.DataFrame:
    mapa = pd.DataFrame([
        [nome, indicador, direcao, scenario.component_weights[nome]]
        for nome, (indicador, direcao) in COMPONENTES.items()
    ], columns=["COMPONENTE", "INDICADOR", "DIRECAO", "PESO"])
    cols = ["OBS_ID", *METADADOS, *METADADOS_FONTE, "ELEGIBILIDADE_UNIVERSO"]
    colunas_razoes = ["OBS_ID", *COLUNAS_INDICADOR]
    componentes = observacoes[cols].merge(mapa, how="cross").merge(
        razoes[colunas_razoes], how="left", on=["OBS_ID", "INDICADOR"], validate="one_to_one",
    )
    componentes["SITUACAO"] = componentes["SITUACAO"].fillna("indicador_ausente")
    componentes["A_CONTABIL"] = [diagnostico_contabil(*linha) for linha in componentes[[
        "SITUACAO", "FONTES", "ID_DOC", "INDICADOR"
    ]].itertuples(index=False, name=None)]
    valores = componentes["VALOR"].to_numpy(dtype=float, na_value=np.nan)
    componentes["DISPONIVEL"] = componentes["SITUACAO"].eq("valido") & np.isfinite(valores)
    componentes["VALOR_ORIENTADO"] = valores * componentes["DIRECAO"].to_numpy(dtype=int)
    componentes["MACROSETOR"] = componentes["SETOR_FCA"].map(ROTULO_MACRO)
    aptas = componentes.loc[componentes["DISPONIVEL"] & componentes["A_CONTABIL"].eq(LINHAGEM_OK)
                            & componentes["ELEGIBILIDADE_UNIVERSO"].eq("elegivel")].copy()
    aptas["VALOR"] = aptas["VALOR_ORIENTADO"]
    exatas = {chave: _Pares(serie, chave, scenario) for chave, serie in agrupar_referencias(aptas, CHAVE_EXATA).items()}
    macros = {chave: _Pares(serie, chave, scenario) for chave, serie in agrupar_referencias(aptas, CHAVE_MACRO).items()} if scenario.macro else {}

    estatisticas = []
    for linha in componentes.itertuples(index=False):
        prefixo = (linha.ANO_ARQUIVO, linha.ESCOPO, linha.COMPONENTE)
        valor = linha.VALOR_ORIENTADO if linha.DISPONIVEL else np.nan
        grupo = linha.SETOR_FCA
        tipo = "setor_exato"
        estat = _referencia(linha.CD_CVM, valor, exatas.get((*prefixo, grupo)), scenario.method)
        exata_status, exata_n = estat["S_ESTATISTICO"], estat["N_PARES"]
        chave_macro = (*prefixo, linha.MACROSETOR)
        if exata_status != "utilizavel" and chave_macro in macros:
            estat = _referencia(linha.CD_CVM, valor, macros[chave_macro], scenario.method)
            grupo, tipo = linha.MACROSETOR, "macrosetor_candidato"
        motivos = [motivo for motivo in (
            None if linha.ELEGIBILIDADE_UNIVERSO == "elegivel" else linha.ELEGIBILIDADE_UNIVERSO,
            None if linha.DISPONIVEL else linha.SITUACAO if linha.SITUACAO != "valido" else "valor_nao_finito",
            None if linha.A_CONTABIL == LINHAGEM_OK else linha.A_CONTABIL,
            None if estat["S_ESTATISTICO"] == "utilizavel" else estat["S_ESTATISTICO"],
        ) if motivo is not None]
        if motivos:
            estat["PONTOS"] = np.nan
        assinatura = estat.get("REFERENCIA_SHA256")
        estat.update(
            REFERENCIA_TIPO=tipo, REFERENCIA_GRUPO=grupo, REFERENCIA_ANO=linha.ANO_ARQUIVO, REFERENCIA_ESCOPO=linha.ESCOPO,
            N_PARES_SETOR_EXATO=exata_n, STATUS_SETOR_EXATO=exata_status,
            ID_REFERENCIA=hash_canonico([config_id, *prefixo, grupo, tipo, assinatura]) if assinatura else None,
            MOTIVOS_COMPONENTE=json.dumps(list(dict.fromkeys(motivos)), ensure_ascii=False),
        )
        estatisticas.append(estat)
    return pd.concat([componentes.reset_index(drop=True), pd.DataFrame(estatisticas)], axis=1)


def calculate_scores(painel: pd.DataFrame, scenario: Scenario = Scenario()) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retorna observações e linhagem dos cinco componentes, preservando eixos independentes."""
    validadas = painel["MODO_TEMPORAL"].eq(MODO_TEMPORAL).fillna(False)
    if painel.empty or not validadas.all():
        raise ValueError("O cálculo experimental exige um painel descritivo revisado não vazio.")
    if painel[UNIDADE].isna().any().any() or not painel["ESCOPO"].isin(("con", "ind")).all():
        raise ValueError("O painel tem chave anual ausente ou escopo desconhecido.")
    ano_fiscal = pd.to_datetime(painel["DT_REFER"]).dt.year
    if (ano_fiscal.notna() & ~ano_fiscal.eq(painel["ANO_ARQUIVO"])).any():
        raise ValueError("O exercício contábil diverge do ano da partição.")
    observacoes, razoes = _selecionar_documentos(painel)
    observacoes["ELEGIBILIDADE_UNIVERSO"] = _elegibilidade(observacoes, scenario)
    config_id = scenario.config_id
    componentes = _calcular_componentes(observacoes, razoes, scenario, config_id)
    valores = razoes.pivot(index="OBS_ID", columns="INDICADOR", values="VALOR").reindex(columns=PROTOTIPOS)
    observacoes = observacoes.join(valores.rename(columns=str.upper), on="OBS_ID")
    caixa = razoes.loc[razoes["INDICADOR"].eq(PRESSAO)].set_index("OBS_ID")
    observacoes["MARCADOR_CAIXA"] = [
        _marcador_caixa(caixa.at[obs.OBS_ID, "FONTES"], obs.ID_DOC) if obs.OBS_ID in caixa.index else "caixa_nao_verificado"
        for obs in observacoes.itertuples(index=False)
    ]
    pl = componentes.loc[componentes["COMPONENTE"].eq("D2")].set_index("OBS_ID")
    observacoes["PATRIMONIO_LIQUIDO_NEGATIVO"] = (
        pl["VALOR"].lt(0).where(pl["DISPONIVEL"] & pl["A_CONTABIL"].eq(LINHAGEM_OK)).astype("boolean")
    ).reindex(observacoes["OBS_ID"]).array
    pontos = componentes.pivot(index="OBS_ID", columns="COMPONENTE", values="PONTOS")
    motivos = componentes.pivot(index="OBS_ID", columns="COMPONENTE", values="MOTIVOS_COMPONENTE")
    prefixo = "PERCENTIL" if scenario.method == "percentil" else "PONTOS_ROBUSTOS"
    observacoes = observacoes.join(pontos.add_prefix(f"{prefixo}_"), on="OBS_ID")
    campos_referencia = {"REFERENCIA_TIPO": "REF_TIPO", "REFERENCIA_GRUPO": "REF_GRUPO", "N_PARES": "N_PARES"}
    for coluna, prefixo_ref in campos_referencia.items():
        referencia = componentes.pivot(index="OBS_ID", columns="COMPONENTE", values=coluna)
        observacoes = observacoes.join(referencia.add_prefix(f"{prefixo_ref}_"), on="OBS_ID")
    pesos = scenario.component_weights
    for eixo, codigos, coluna in (("QUALITY", ["Q1", "Q2"], "QUALITY_SCORE"), ("DISTRESS", ["D1", "D2", "D3"], "FINANCIAL_DISTRESS_SCORE")):
        fatia = componentes.loc[componentes["COMPONENTE"].isin(codigos)].copy()
        contrib = pontos[codigos].mul([pesos[c] for c in codigos], axis="columns")
        score = contrib.sum(axis=1, min_count=len(codigos)).clip(0.0, 100.0)
        observacoes[coluna] = score.reindex(observacoes["OBS_ID"]).array
        observacoes[f"STATUS_{eixo}"] = np.where(observacoes[coluna].notna(), "calculado", "bloqueado")
        com_macro = observacoes[[f"REF_TIPO_{c}" for c in codigos]].eq("macrosetor_candidato").sum(axis=1)
        observacoes[f"COMPOSICAO_REFERENCIA_{eixo}"] = np.select([
            observacoes[coluna].isna(), com_macro.eq(0), com_macro.eq(len(codigos)),
        ], ["nao_calculado", "setor_exato", "macrosetor_candidato"], default="mista")
        peso_disponivel = fatia["PESO"].where(fatia["DISPONIVEL"], 0.0)
        cobertura = peso_disponivel.groupby(fatia["OBS_ID"]).sum()
        observacoes[f"DISPONIBILIDADE_{eixo}"] = cobertura.reindex(observacoes["OBS_ID"]).array
        observacoes[f"PESOS_{eixo}"] = json.dumps({c: pesos[c] for c in codigos}, sort_keys=True)
        observacoes[f"MOTIVOS_{eixo}"] = [
            json.dumps({c: json.loads(m) for c, m in zip(codigos, linha, strict=True) if m != "[]"}, ensure_ascii=False)
            for linha in motivos[codigos].reindex(observacoes["OBS_ID"]).itertuples(index=False, name=None)
        ]

    metadados = {
        "CENARIO": scenario.name, "VERSAO_METODOLOGICA": VERSAO_METODOLOGICA, "CONFIG_ID": config_id,
        "METODO_NORMALIZACAO": scenario.method, "MIN_PARES": scenario.min_peers,
        "MODO_TEMPORAL": MODO_TEMPORAL, "ELEGIBILIDADE_TEMPORAL": "bloqueada_sem_evidencia",
    }
    observacoes["EXERCICIO"] = pd.to_datetime(observacoes["DT_REFER"]).dt.year.astype("Int64")
    componentes["EXERCICIO"] = pd.to_datetime(componentes["DT_REFER"]).dt.year.astype("Int64")
    return observacoes.drop(columns="OBS_ID").assign(**metadados), componentes.drop(columns="OBS_ID").assign(**metadados)
