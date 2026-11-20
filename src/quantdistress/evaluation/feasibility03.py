"""Experimentos agregados de elegibilidade e escolhas contábeis da Sprint 03A."""

import argparse
import json
from decimal import Decimal, localcontext
from pathlib import Path

import pandas as pd

from quantdistress.data._snapshot import gravar_json, ler_json, sha256
from quantdistress.data.dfp import FATORES_ESCALA
from quantdistress.data.universe import CHAVE_OBSERVACAO, CHAVE_REFERENCIA
from quantdistress.features.indicators import PROTOTIPOS

CHAVE = ["ANO_ARQUIVO", *CHAVE_OBSERVACAO]
Q_NUCLEO = ("rentabilidade_operacional_ativos", "fluxo_caixa_operacional_sobre_receita")
D_NUCLEO = ("liquidez_corrente", "patrimonio_liquido_sobre_ativo", "financiamentos_reportados_sobre_ativo")
Q_TODOS = tuple(nome for nome, regra in PROTOTIPOS.items() if regra.eixo == "quality")
D_TODOS = tuple(nome for nome, regra in PROTOTIPOS.items() if regra.eixo == "distress")
PRESSAO = "financiamentos_circulantes_sobre_caixa"
NIVEIS = {
    "ano_escopo": ["ANO_ARQUIVO", "ESCOPO"],
    "ano_setor_escopo": ["ANO_ARQUIVO", "ESCOPO", "GRUPO_SETORIAL", "SETOR_FCA"],
    "periodo_escopo": ["ESCOPO"],
    "periodo_setor_escopo": ["ESCOPO", "GRUPO_SETORIAL", "SETOR_FCA"],
}


def selecionar_referencias(observacoes: pd.DataFrame) -> pd.Series:
    """Marca uma única última referência por código CVM, ano e escopo, antes dos filtros."""
    chave = ["ANO_ARQUIVO", "CD_CVM", "ESCOPO"]
    ultima = observacoes.groupby(chave)["DT_REFER"].transform("max")
    candidatas = observacoes["DT_REFER"].eq(ultima)
    contagem = candidatas.groupby([observacoes[coluna] for coluna in chave]).transform("sum")
    return candidatas & contagem.eq(1)


def cenarios_cobertura(valores: pd.DataFrame, caixa_zero_com_financiamento: pd.Series) -> pd.DataFrame:
    """Testa presença simultânea de variáveis, sem calcular índices ou imputar valores."""
    presentes = valores.notna()
    q = presentes[list(Q_TODOS)].sum(axis=1)
    d = presentes[list(D_TODOS)].sum(axis=1)
    q_nucleo = presentes[list(Q_NUCLEO)].all(axis=1)
    d_nucleo = presentes[list(D_NUCLEO)].all(axis=1)
    return pd.DataFrame({
        "q_3_de_5_quaisquer": q.ge(3),
        "q_4_de_5_quaisquer": q.ge(4),
        "q_5_de_5": q.eq(5),
        "q_nucleo_2_de_2": q_nucleo,
        "q_nucleo_mais_uma": q_nucleo & q.ge(3),
        "d_2_de_4_quaisquer": d.ge(2),
        "d_3_de_4_quaisquer": d.ge(3),
        "d_4_de_4": d.eq(4),
        "d_nucleo_3_de_3": d_nucleo,
        "d_nucleo_mais_pressao_ou_estado_caixa_zero": d_nucleo & (
            presentes[PRESSAO] | caixa_zero_com_financiamento
        ),
        "ambos_nucleos": q_nucleo & d_nucleo,
        "ambas_baterias_completas": q.eq(5) & d.eq(4),
    }, index=valores.index)


def _valor(fonte: dict) -> Decimal:
    with localcontext() as contexto:
        contexto.prec = 38
        return Decimal(fonte["VL_CONTA"]) * FATORES_ESCALA[fonte["ESCALA_MOEDA"]]


def _extrair_experimentos(indicadores: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    variantes = {
        "rentabilidade_operacional_ativos": "resultado_sobre_ativo_final",
        "giro_ativo": "receita_sobre_ativo_final",
        "financiamentos_reportados_sobre_ativo": "financiamento_circulante_sobre_ativo",
    }
    selectos = indicadores.loc[indicadores["INDICADOR"].isin([*variantes, *Q_NUCLEO, PRESSAO])]
    caixa, pares, dfc = [], [], []
    for linha in selectos[[*CHAVE, "INDICADOR", "SITUACAO", "VALOR", "FONTES"]].itertuples(index=False, name=None):
        *chave, nome, situacao, valor, fontes = linha
        if nome == PRESSAO and situacao == "denominador_invalido":
            curto, saldo = map(_valor, json.loads(fontes))
            if saldo == 0:
                caixa.append([*chave, "com_financiamento" if curto > 0 else "sem_financiamento"])
        if situacao != "valido":
            continue
        if nome in variantes:
            numerador, ativo, terceiro = map(_valor, json.loads(fontes))
            base = terceiro if nome == "financiamentos_reportados_sobre_ativo" else ativo
            if base > 0:
                pares.append([*chave, variantes[nome], float(valor), float(numerador / base)])
        if nome == Q_NUCLEO[1]:
            metodo = json.loads(fontes)[0]["FAMILIA"]
            dfc.append([*chave, metodo, float(valor)])
    return (
        pd.DataFrame(caixa, columns=[*CHAVE, "ESTADO_CAIXA_ZERO"]),
        pd.DataFrame(pares, columns=[*CHAVE, "VARIANTE", "ORIGINAL", "ALTERNATIVA"]),
        pd.DataFrame(dfc, columns=[*CHAVE, "METODO_DFC", "CAIXA_SOBRE_RECEITA"]),
    )


def _referencias_consolidadas(pasta: Path) -> pd.DataFrame:
    arquivo = pasta / "fatos.parquet"
    manifesto = ler_json(pasta / "manifesto.json")
    if sha256(arquivo) != manifesto["tabelas"]["fatos"]["sha256"]:
        raise ValueError(f"Parquet DFP divergente do manifesto: {arquivo}")
    fatos = pd.read_parquet(
        arquivo, columns=CHAVE_REFERENCIA,
        filters=[("ESCOPO", "=", "con"), ("ORDEM_EXERC", "=", "ÚLTIMO")],
    )
    return fatos[CHAVE_REFERENCIA].drop_duplicates().assign(CONSOLIDADO_NA_FONTE=True)


def _carregar(painel: Path, dados: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    manifesto = ler_json(painel / "manifesto.json")
    if manifesto["modo_temporal"] != "descritivo_revisado":
        raise ValueError("Esperado o painel descritivo revisado da Sprint 02.")
    universos, quadros = [], []
    for captura in manifesto["anos"]:
        ano = captura["ano"]
        h = captura["fonte_dfp"]["sha256"]
        pasta = painel / str(ano)
        universo = pd.read_parquet(pasta / "universo.parquet")
        quadro = pd.read_parquet(pasta / "indicadores.parquet", columns=[*CHAVE, "INDICADOR", "SITUACAO", "VALOR", "FONTES", "SHA256_DFP"])
        for tabela in (universo, quadro):
            if not (tabela["SHA256_DFP"].eq(h) & tabela["ANO_ARQUIVO"].eq(ano)).all():
                raise ValueError(f"Partição incompatível com o manifesto: {ano}.")
        bruto = _referencias_consolidadas(dados / "interim" / "dfp" / str(ano) / h)
        universos.append(universo.merge(bruto, how="left", on=CHAVE_REFERENCIA, validate="many_to_one"))
        quadros.append(quadro)
    return pd.concat(universos, ignore_index=True), pd.concat(quadros, ignore_index=True)


def _resumir_grupos(tabela: pd.DataFrame, flags: list[str]) -> pd.DataFrame:
    agregacao = {campo: (campo, "sum") for campo in flags}
    por_emissor = {f"EMISSORES_{campo}": tabela["CD_CVM"].where(tabela[campo]) for campo in flags}
    agregacao.update({campo: (campo, "nunique") for campo in por_emissor})
    tabela = tabela.assign(**por_emissor)
    return pd.concat([
        tabela.groupby(chaves, dropna=False).agg(
            OBSERVACOES=("CD_CVM", "size"), EMISSORES_CVM=("CD_CVM", "nunique"), **agregacao,
        ).reset_index().assign(NIVEL=nivel)
        for nivel, chaves in NIVEIS.items()
    ], ignore_index=True)


def _resumir_variantes(pares: pd.DataFrame) -> pd.DataFrame:
    pares = pares.assign(DIF_ABS=pares["ALTERNATIVA"].sub(pares["ORIGINAL"]).abs())
    registros = []
    for nivel, chaves in NIVEIS.items():
        chaves = [*chaves, "VARIANTE"]
        for chave, grupo in pares.groupby(chaves, dropna=False):
            rho = None
            if len(grupo) >= 10 and grupo["CD_CVM"].nunique() >= 10 and grupo[["ORIGINAL", "ALTERNATIVA"]].nunique().gt(1).all():
                rho = grupo["ORIGINAL"].rank().corr(grupo["ALTERNATIVA"].rank())
            registros.append({
                **dict(zip(chaves, chave, strict=True)), "NIVEL": nivel,
                "OBSERVACOES": len(grupo), "EMISSORES_CVM": grupo["CD_CVM"].nunique(),
                "MEDIANA_ORIGINAL": grupo["ORIGINAL"].median(), "MEDIANA_ALTERNATIVA": grupo["ALTERNATIVA"].median(),
                "MEDIANA_DIF_ABS": grupo["DIF_ABS"].median(), "P90_DIF_ABS": grupo["DIF_ABS"].quantile(.9),
                "SPEARMAN": rho,
            })
    return pd.DataFrame(registros)


def _cobertura_pares_exatos(base: pd.DataFrame) -> pd.DataFrame:
    chaves = ["ANO_ARQUIVO", "ESCOPO", "SETOR_FCA"]
    pares, dispersoes = {}, {}
    for nome in (*Q_NUCLEO, *D_NUCLEO):
        validos = base.dropna(subset=[nome, "SETOR_FCA"])
        grupo = validos.groupby(chaves)[nome]
        pares[nome] = grupo.transform("count").sub(1)
        unicos = grupo.transform("nunique")
        mesma_medida = validos.groupby([*chaves, nome])[nome].transform("count")
        dispersoes[nome] = unicos.gt(2) | (unicos.eq(2) & mesma_medida.gt(1))
    pares = pd.DataFrame(pares, index=base.index).fillna(0)
    dispersao = pd.DataFrame(dispersoes, index=base.index).eq(True)
    resumo = []
    for minimo in (15, 30, 50):
        referencias = pares.ge(minimo) & dispersao
        com_q = referencias[list(Q_NUCLEO)].all(axis=1)
        com_d = referencias[list(D_NUCLEO)].all(axis=1)
        flags = ["Q_PARES", "D_PARES", "AMBOS_PARES"]
        tabela = base.assign(Q_PARES=com_q, D_PARES=com_d, AMBOS_PARES=com_q & com_d)
        resumo.append(_resumir_grupos(tabela, flags).assign(MIN_PARES_EXCLUINDO_ALVO=minimo))
    return pd.concat(resumo, ignore_index=True)


def experimentar(painel: Path, dados: Path) -> dict[str, pd.DataFrame]:
    universo, indicadores = _carregar(painel, dados)
    if universo.duplicated(CHAVE).any() or indicadores.duplicated([*CHAVE, "INDICADOR"]).any():
        raise ValueError("Chaves duplicadas no painel de entrada.")
    validade = indicadores["SITUACAO"].eq("valido")
    finitos = indicadores["VALOR"].notna() & ~indicadores["VALOR"].isin([float("inf"), float("-inf")])
    if not validade.eq(finitos).all():
        raise ValueError("Valores e situações inconsistentes no painel.")
    valores = indicadores.pivot(index=CHAVE, columns="INDICADOR", values="VALOR").reindex(columns=list(PROTOTIPOS))
    base = universo.merge(valores, on=CHAVE, how="left", validate="one_to_one")
    caixa, pares, dfc = _extrair_experimentos(indicadores)
    base = base.merge(caixa, on=CHAVE, how="left", validate="one_to_one")
    base["HOLDING_FCA"] = base["SETOR_FCA"].str.startswith("Emp. Adm. Part. - ", na=False)
    base["REF_ESCOLHIDA"] = selecionar_referencias(base)
    base["ENTREGA_UNICA"] = base["REF_ESCOLHIDA"] & base["SITUACAO_ENTREGA_DFP"].eq("unica")
    base["NAO_FINANCEIRA"] = base["ENTREGA_UNICA"] & base["GRUPO_SETORIAL"].eq("nao_financeira")
    base["SEM_HOLDING"] = base["NAO_FINANCEIRA"] & ~base["HOLDING_FCA"]
    base["CAIXA_ZERO_COM_FINANCIAMENTO"] = base["ESTADO_CAIXA_ZERO"].eq("com_financiamento")
    base["CAIXA_ZERO_SEM_FINANCIAMENTO"] = base["ESTADO_CAIXA_ZERO"].eq("sem_financiamento")
    base["PL_NEGATIVO_VALIDADO"] = base["patrimonio_liquido_sobre_ativo"].lt(0).fillna(False)
    base["SEM_DATA_DIVULGACAO"] = base["DT_DIVULGACAO"].isna()
    base["CONSOLIDADO_NA_FONTE"] = base["CONSOLIDADO_NA_FONTE"].eq(True)
    flags = [
        "HOLDING_FCA", "REF_ESCOLHIDA", "ENTREGA_UNICA", "NAO_FINANCEIRA", "SEM_HOLDING",
        "CONSOLIDADO_NA_FONTE", "CAIXA_ZERO_COM_FINANCIAMENTO", "CAIXA_ZERO_SEM_FINANCIAMENTO",
        "PL_NEGATIVO_VALIDADO", "SEM_DATA_DIVULGACAO",
    ]
    coortes = {
        "nao_financeira_referencia_unica": base["NAO_FINANCEIRA"],
        "nao_financeira_sem_holdings": base["SEM_HOLDING"],
        "nao_financeira_ind_sem_con_na_fonte": (
            base["NAO_FINANCEIRA"] & base["ESCOPO"].eq("ind") & ~base["CONSOLIDADO_NA_FONTE"]
        ),
        "nao_financeira_ind_sem_con_e_sem_holdings": (
            base["SEM_HOLDING"] & base["ESCOPO"].eq("ind") & ~base["CONSOLIDADO_NA_FONTE"]
        ),
        "nao_financeira_holdings": base["NAO_FINANCEIRA"] & base["HOLDING_FCA"],
    }
    cenarios = cenarios_cobertura(base, base["CAIXA_ZERO_COM_FINANCIAMENTO"])
    base = pd.concat([base, cenarios], axis=1)
    medidas = list(cenarios.columns)
    elegibilidade = pd.concat([
        _resumir_grupos(base.loc[mascara], medidas).assign(COORTE=coorte)
        for coorte, mascara in coortes.items()
    ], ignore_index=True)
    grupo = base.loc[base["NAO_FINANCEIRA"], [*CHAVE, "GRUPO_SETORIAL", "SETOR_FCA"]]
    pares = pares.merge(grupo, on=CHAVE, how="inner", validate="many_to_one")
    dfc = dfc.merge(grupo, on=CHAVE, how="inner", validate="many_to_one")
    metodos = dfc.groupby(["ANO_ARQUIVO", "ESCOPO", "SETOR_FCA", "METODO_DFC"], dropna=False).agg(
        OBSERVACOES=("CD_CVM", "size"), EMISSORES_CVM=("CD_CVM", "nunique"),
        MEDIANA_CAIXA_SOBRE_RECEITA=("CAIXA_SOBRE_RECEITA", "median"),
    ).reset_index()
    return {
        "exclusoes_e_estados": _resumir_grupos(base, flags),
        "estados_referencia_escolhida": _resumir_grupos(base.loc[base["REF_ESCOLHIDA"]], flags),
        "experimentos_cobertura": elegibilidade,
        "viabilidade_pares_exatos": _cobertura_pares_exatos(base.loc[base["NAO_FINANCEIRA"]]),
        "sensibilidade_contabil": _resumir_variantes(pares),
        "metodos_dfc": metodos,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Executa experimentos agregados da Sprint 03A.")
    parser.add_argument("--painel", type=Path, default=Path("data/processed/sprint02"))
    parser.add_argument("--dados", type=Path, default=Path("data"))
    parser.add_argument("--saida", type=Path, default=Path("outputs/sprint03a-viabilidade"))
    args = parser.parse_args()
    tabelas = experimentar(args.painel, args.dados)
    args.saida.mkdir(parents=True, exist_ok=True)
    for nome, tabela in tabelas.items():
        tabela.to_csv(args.saida / f"{nome}.csv", index=False)
    gravar_json(args.saida / "manifesto.json", {
        "sha256_manifesto_painel": sha256(args.painel / "manifesto.json"),
        "modo_temporal": "descritivo_revisado",
        "tabelas": {nome: len(tabela) for nome, tabela in tabelas.items()},
    })
    print(args.saida.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
