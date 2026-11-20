"""Sensibilidade descritiva dos eixos e das convenções da matriz experimental."""

from dataclasses import replace

import numpy as np
import pandas as pd

CHAVE = ["ANO_ARQUIVO", "ESCOPO", "CD_CVM"]
EIXOS = ("QUALITY_SCORE", "FINANCIAL_DISTRESS_SCORE")
MODO = "descritivo_revisado"
FAIXAS = ("Q<·D<", "Q<·D≥", "Q≥·D<", "Q≥·D≥")
RECORTES = {
    "periodo_escopo": ["ESCOPO"],
    "ano_escopo": ["ANO_ARQUIVO", "ESCOPO"],
    "ano_setor_escopo": ["ANO_ARQUIVO", "SETOR_FCA", "ESCOPO"],
}
CORTES = (40, 50, 60)


def cenarios_sensibilidade(benchmark):
    """Altera uma escolha de cada vez, mantendo fixas as demais opções."""
    return (
        replace(benchmark, name="pesos_economicos", weights="economicos"),
        replace(benchmark, name="macrosetores_candidatos", macro=True),
        replace(benchmark, name="z_robusto", method="robusto"),
        replace(benchmark, name="sem_holdings", holdings=False),
        replace(benchmark, name="pares_15", min_peers=15),
        replace(benchmark, name="pares_50", min_peers=50),
        replace(benchmark, name="retirada_20pct", composition="retirada_20pct"),
        replace(benchmark, name="retirada_20pct_b", composition="retirada_20pct_b"),
    )


def _validar(scores: pd.DataFrame) -> None:
    if scores.duplicated(CHAVE).any() or scores[CHAVE].isna().any().any():
        raise ValueError("O painel exige uma observação por CVM, ano e escopo.")
    if not scores["ESCOPO"].isin(("con", "ind")).all():
        raise ValueError("O painel deve preservar o escopo con ou ind.")
    if not scores["MODO_TEMPORAL"].eq(MODO).fillna(False).all():
        raise ValueError("Esperado somente o modo descritivo_revisado.")
    for eixo in EIXOS:
        valores = scores[eixo].dropna().to_numpy(dtype=float)
        if not np.isfinite(valores).all() or ((valores < -1e-12) | (valores > 100 + 1e-12)).any():
            raise ValueError(f"Valores fora da escala para {eixo}.")


def _grupos(tabela):
    for nivel, campos in RECORTES.items():
        for chave, grupo in tabela.groupby(campos, dropna=False):
            yield {"NIVEL": nivel, **dict(zip(campos, chave, strict=True))}, grupo


def cobertura(scores: pd.DataFrame, cenario: str) -> pd.DataFrame:
    """Conta o universo documental e as observações com cada eixo e com ambos."""
    _validar(scores)
    linhas = []
    for chaves, grupo in _grupos(scores):
        q = grupo[EIXOS[0]].notna()
        d = grupo[EIXOS[1]].notna()
        linhas.append({
            **chaves, "CENARIO": cenario, "OBSERVACOES": len(grupo), "EMISSORES_CVM": grupo.CD_CVM.nunique(),
            "QUALITY": int(q.sum()), "DISTRESS": int(d.sum()), "AMBOS": int((q & d).sum()),
            "EMISSORES_AMBOS": grupo.loc[q & d, "CD_CVM"].nunique(),
        })
    return pd.DataFrame(linhas)


def quadrantes(quality: pd.Series, distress: pd.Series, corte: float) -> pd.Series:
    """Posição geométrica em relação ao corte, sem rótulos de qualidade ou risco."""
    q = quality.to_numpy(dtype=float, na_value=np.nan)
    d = distress.to_numpy(dtype=float, na_value=np.nan)
    lado_q = (q >= corte) | np.isclose(q, corte, rtol=0, atol=1e-12)
    lado_d = (d >= corte) | np.isclose(d, corte, rtol=0, atol=1e-12)
    lado = np.array(FAIXAS, dtype=object)[2 * lado_q.astype(int) + lado_d.astype(int)]
    return pd.Series(lado, index=quality.index).where(np.isfinite(q) & np.isfinite(d))


def _parear(base, alternativa) -> pd.DataFrame:
    _validar(base)
    _validar(alternativa)
    identidades = ("CNPJ_CIA", "SETOR_FCA", "DT_REFER")
    campos = [*CHAVE, *identidades, *EIXOS]
    pares = base[campos].merge(
        alternativa[campos], on=CHAVE, how="outer", validate="one_to_one", indicator=True, suffixes=("_BASE", "_ALT"),
    )
    if not pares["_merge"].eq("both").all():
        raise ValueError("A sensibilidade exige o mesmo universo documental nos cenários.")
    for campo in identidades:
        a, b = pares[f"{campo}_BASE"], pares[f"{campo}_ALT"]
        mesmo = a.eq(b).fillna(False) | (a.isna() & b.isna())
        if not mesmo.all():
            raise ValueError(f"Mudança da observação de origem entre cenários em {campo}.")
    return pares.assign(SETOR_FCA=pares["SETOR_FCA_BASE"])


def _deltas(pares: pd.DataFrame, cenario: str, amostra: str = "pares_por_cenario") -> pd.DataFrame:
    linhas = []
    for chaves, grupo in _grupos(pares):
        for eixo in EIXOS:
            a, b = grupo[f"{eixo}_BASE"], grupo[f"{eixo}_ALT"]
            ambas = a.notna() & b.notna()
            delta = b[ambas].astype(float) - a[ambas].astype(float)
            rho = np.nan
            if a[ambas].nunique() > 1 and b[ambas].nunique() > 1:
                rho = a[ambas].rank().corr(b[ambas].rank())
            linhas.append({
                **chaves, "CENARIO": cenario, "EIXO": eixo, "AMOSTRA": amostra, "OBSERVACOES": len(grupo),
                "PAREADAS": int(ambas.sum()), "EMISSORES_PAREADOS": grupo.loc[ambas, "CD_CVM"].nunique(),
                "SO_BASE": int((a.notna() & b.isna()).sum()), "SO_CENARIO": int((b.notna() & a.isna()).sum()),
                "MEDIANA_DELTA_PONTOS": delta.median(), "MEDIANA_ABS_PONTOS": delta.abs().median(),
                "P90_ABS_PONTOS": delta.abs().quantile(.9), "SPEARMAN_PAREADO": rho,
            })
    return pd.DataFrame(linhas)


def _transicoes(pares: pd.DataFrame, cenario: str, cortes: tuple[tuple[int, int], ...], amostra: str = "pares_por_cenario"):
    transicoes, estabilidade = [], []
    for corte_base, corte_alt in cortes:
        dados = pares.assign(
            QUADRANTE_BASE=quadrantes(pares[f"{EIXOS[0]}_BASE"], pares[f"{EIXOS[1]}_BASE"], corte_base),
            QUADRANTE_CENARIO=quadrantes(pares[f"{EIXOS[0]}_ALT"], pares[f"{EIXOS[1]}_ALT"], corte_alt),
        )
        for chaves, grupo in _grupos(dados):
            a, b = grupo.QUADRANTE_BASE, grupo.QUADRANTE_CENARIO
            ambos = a.notna() & b.notna()
            mudaram = int(a[ambos].ne(b[ambos]).sum())
            n = int(ambos.sum())
            chave = {**chaves, "CENARIO": cenario, "AMOSTRA": amostra, "CORTE_BASE": corte_base, "CORTE_CENARIO": corte_alt}
            estabilidade.append({
                **chave, "PAREADAS": n, "MUDARAM": mudaram, "PROPORCAO_MUDANCA": mudaram / n if n else np.nan,
                "SO_BASE": int((a.notna() & b.isna()).sum()), "SO_CENARIO": int((b.notna() & a.isna()).sum()),
            })
            contagens = grupo.loc[ambos].groupby(["QUADRANTE_BASE", "QUADRANTE_CENARIO"]).size()
            transicoes.extend({**chave, "QUADRANTE_BASE": antes, "QUADRANTE_CENARIO": depois, "OBSERVACOES": total}
                             for (antes, depois), total in contagens.items())
    return pd.DataFrame(estabilidade), pd.DataFrame(transicoes)


def _matriz_quadrantes(base: pd.DataFrame) -> pd.DataFrame:
    quadros = []
    for corte in CORTES:
        quadrante = quadrantes(base[EIXOS[0]], base[EIXOS[1]], corte)
        for chaves, grupo in _grupos(base.assign(QUADRANTE=quadrante)):
            contagens = grupo.QUADRANTE.value_counts().reindex(FAIXAS, fill_value=0)
            quadros.extend({**chaves, "CORTE": corte, "QUADRANTE": faixa, "OBSERVACOES": total}
                           for faixa, total in contagens.items())
    return pd.DataFrame(quadros)


def analisar_sensibilidade(base: pd.DataFrame, alternativas: dict[str, pd.DataFrame], nome_base: str):
    """Compara eixos por pares e quadrantes na interseção dos dois eixos nos dois cenários."""
    tabelas_cobertura = [cobertura(base, nome_base)]
    deltas, estabilidade, transicoes = [], [], []
    cortes_iguais = tuple((corte, corte) for corte in CORTES)
    pareamentos = {nome: _parear(base, scores) for nome, scores in alternativas.items()}
    for nome, scores in alternativas.items():
        pares = pareamentos[nome]
        tabelas_cobertura.append(cobertura(scores, nome))
        deltas.append(_deltas(pares, nome))
        diagnostico, mudancas = _transicoes(pares, nome, cortes_iguais)
        estabilidade.append(diagnostico)
        transicoes.append(mudancas)
    comparaveis = ("pesos_economicos", "z_robusto")
    if all(nome in pareamentos for nome in comparaveis):
        for nome, outro in (comparaveis, comparaveis[::-1]):
            comum = pareamentos[nome].set_index(CHAVE)
            terceira = pareamentos[outro].set_index(CHAVE).reindex(comum.index)
            for eixo in EIXOS:
                colunas = [f"{eixo}_BASE", f"{eixo}_ALT"]
                manter = comum[colunas].notna().all(axis=1) & terceira[colunas].notna().all(axis=1)
                comum.loc[~manter, colunas] = np.nan
            comum = comum.reset_index()
            amostra = "comum_benchmark_pesos_metodo"
            deltas.append(_deltas(comum, nome, amostra))
            diagnostico, mudancas = _transicoes(comum, nome, cortes_iguais, amostra)
            estabilidade.append(diagnostico)
            transicoes.append(mudancas)
    diagnostico, mudancas = _transicoes(_parear(base, base), "convencao_corte", ((50, 40), (50, 60)))
    estabilidade.append(diagnostico)
    transicoes.append(mudancas)
    return {
        "sensibilidade_cobertura": pd.concat(tabelas_cobertura, ignore_index=True),
        "sensibilidade_scores": pd.concat(deltas, ignore_index=True) if deltas else pd.DataFrame(),
        "estabilidade_quadrantes": pd.concat(estabilidade, ignore_index=True),
        "transicoes_quadrantes": pd.concat(transicoes, ignore_index=True),
        "matriz_quadrantes": _matriz_quadrantes(base),
    }
