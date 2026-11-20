"""Diagnósticos agregados dos indicadores descritivos da Sprint 02."""

import argparse
import json
from collections.abc import Iterator
from decimal import Decimal, localcontext
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

from quantdistress.data.dfp import FATORES_ESCALA
from quantdistress.features.indicators import ANTERIOR, ATUAL, CHAVE_PAINEL, PROTOTIPOS

CHAVE_OBSERVACAO = ["ANO_ARQUIVO", *CHAVE_PAINEL]
COLUNAS_SETOR = ["GRUPO_SETORIAL", "SETOR_FCA"]
COLUNAS_LEITURA = [*CHAVE_OBSERVACAO, *COLUNAS_SETOR, "INDICADOR", "VALOR", "SITUACAO", "FONTES"]
INDICADORES = tuple(PROTOTIPOS)
INDICADORES_QUALITY = [nome for nome in INDICADORES if PROTOTIPOS[nome].eixo == "quality"]
INDICADORES_DISTRESS = [nome for nome in INDICADORES if PROTOTIPOS[nome].eixo == "distress"]
RECORTES = {
    "ano_setor": ["ANO_ARQUIVO", "ESCOPO", *COLUNAS_SETOR],
    "ano_grupo": ["ANO_ARQUIVO", "ESCOPO", "GRUPO_SETORIAL"],
    "ano": ["ANO_ARQUIVO", "ESCOPO"],
    "periodo_grupo": ["ESCOPO", "GRUPO_SETORIAL"],
    "periodo": ["ESCOPO"],
}
DENOMINADORES = {
    "margem_operacional": (("receita_vendas_servicos", ATUAL),),
    "rentabilidade_operacional_ativos": (("ativo_total", ATUAL), ("ativo_total", ANTERIOR)),
    "fluxo_caixa_operacional_sobre_receita": (("receita_vendas_servicos", ATUAL),),
    "giro_ativo": (("ativo_total", ATUAL), ("ativo_total", ANTERIOR)),
    "crescimento_receita": (("receita_vendas_servicos", ANTERIOR),),
    "liquidez_corrente": (("passivo_circulante", ATUAL),),
    "patrimonio_liquido_sobre_ativo": (("ativo_total", ATUAL),),
    "financiamentos_reportados_sobre_ativo": (("ativo_total", ATUAL),),
    "financiamentos_circulantes_sobre_caixa": (("caixa_equivalentes", ATUAL),),
}


def carregar_indicadores(painel: Path) -> pd.DataFrame:
    """Lê todas as partições listadas no manifesto descritivo, sem baixar dados."""
    manifesto = json.loads((painel / "manifesto.json").read_text(encoding="utf-8"))
    if manifesto["modo_temporal"] != "descritivo_revisado":
        raise ValueError("Esperado o painel no modo descritivo_revisado.")
    anos = manifesto["anos"]
    if not anos or len({item["ano"] for item in anos}) != len(anos):
        raise ValueError("O manifesto deve listar uma única partição por ano presente.")
    particoes = []
    for particao in anos:
        ano = particao["ano"]
        tabela = pd.read_parquet(painel / str(ano) / "indicadores.parquet", columns=COLUNAS_LEITURA)
        if len(tabela) != particao["observacoes_indicadores"] or not tabela["ANO_ARQUIVO"].eq(ano).all():
            raise ValueError(f"Partição de indicadores incompatível com o manifesto em {ano}.")
        particoes.append(tabela)
    return pd.concat(particoes, ignore_index=True)


def matriz_indicadores(tabela: pd.DataFrame) -> pd.DataFrame:
    """Matriz por referência e escopo com valores válidos e todas as observações."""
    chave = CHAVE_OBSERVACAO + ["INDICADOR"]
    if tabela.duplicated(chave).any():
        raise ValueError("O painel contém indicador duplicado na mesma observação.")
    if not tabela["INDICADOR"].isin(INDICADORES).all():
        raise ValueError("O painel contém um indicador desconhecido.")
    valores = tabela["VALOR"].to_numpy(dtype=float, na_value=np.nan)
    if np.isinf(valores).any() or not np.array_equal(
        tabela["SITUACAO"].eq("valido").to_numpy(dtype=bool), np.isfinite(valores),
    ):
        raise ValueError("A situação de validade é incompatível com os valores do painel.")
    meta = tabela[CHAVE_OBSERVACAO + COLUNAS_SETOR].drop_duplicates()
    if meta.duplicated(CHAVE_OBSERVACAO).any():
        raise ValueError("A classificação setorial diverge dentro de uma observação.")
    ampla = tabela.set_index(chave)["VALOR"].unstack("INDICADOR").reindex(columns=INDICADORES).reset_index()
    return ampla.merge(meta, on=CHAVE_OBSERVACAO, how="left", validate="one_to_one")


def _por_recorte(tabela: pd.DataFrame) -> Iterator[tuple[dict, pd.DataFrame]]:
    for nivel, chaves in RECORTES.items():
        for valores, recorte in tabela.groupby(chaves, dropna=False, sort=False, observed=True):
            yield {"NIVEL": nivel, **dict(zip(chaves, valores, strict=True))}, recorte


def _contagem_emissores(codigos: np.ndarray) -> int:
    # O mesmo código CVM conta uma vez no recorte, inclusive com várias datas.
    return int(pd.Series(codigos, dtype="string").nunique())


def _quantis(valores: np.ndarray) -> dict:
    if not len(valores):
        return {}
    minimo, p01, p05, q1, mediana, q3, p95, p99, maximo = np.quantile(
        valores, (0, .01, .05, .25, .5, .75, .95, .99, 1),
    )
    dados = {
        "MINIMO": minimo, "P01": p01, "P05": p05, "Q1": q1, "MEDIANA": mediana,
        "Q3": q3, "P95": p95, "P99": p99, "MAXIMO": maximo, "NEGATIVOS": int((valores < 0).sum()),
        "ZEROS": int((valores == 0).sum()),
    }
    iqr = q3 - q1
    if len(valores) >= 20 and iqr > 0:
        dados.update(
            EXTREMOS_INFERIORES=int((valores < q1 - 3 * iqr).sum()),
            EXTREMOS_SUPERIORES=int((valores > q3 + 3 * iqr).sum()),
        )
    return dados


def _correlacao(pares: np.ndarray, emissores: int, minimo: int) -> dict:
    if len(pares) < minimo or emissores < minimo:
        return {"MOTIVO": "amostra_insuficiente"}
    if np.any(np.ptp(pares, axis=0) == 0):
        return {"MOTIVO": "serie_constante"}

    ranks = pd.DataFrame(pares).rank(method="average").to_numpy()
    coeficientes = {
        "PEARSON": np.corrcoef(pares, rowvar=False)[0, 1],
        "SPEARMAN": np.corrcoef(ranks, rowvar=False)[0, 1],
        "MOTIVO": "calculada",
    }
    if len(pares) >= 20:
        limites = np.quantile(pares, (.01, .99), axis=0)
        winsorizados = np.clip(pares, *limites)
        if np.all(np.ptp(winsorizados, axis=0) > 0):
            coeficientes["PEARSON_WINSOR_P01_P99"] = np.corrcoef(winsorizados, rowvar=False)[0, 1]
    return coeficientes


def _tipo_denominador(indicador: str, situacao: str, fontes: str) -> str:
    # Falhas anteriores à divisão não sustentam inferência de denominador zero.
    if situacao not in {"valido", "denominador_invalido"}:
        return "divisao_nao_avaliada"
    valores = {
        (linha["CONCEITO"], linha["ORDEM_EXERC"]): linha for linha in json.loads(fontes)
    }
    with localcontext() as contexto:
        contexto.prec = 38
        total = sum(
            Decimal(valores[chave]["VL_CONTA"]) * FATORES_ESCALA[valores[chave]["ESCALA_MOEDA"]]
            for chave in DENOMINADORES[indicador]
        )
    # Os dois saldos de ativo formam uma média; a divisão por dois preserva o sinal.
    if total == 0:
        return "zero"
    return "negativo" if total < 0 else "positivo"


def _identidade_ativos(recorte: pd.DataFrame) -> dict:
    tripla = recorte[["CD_CVM", "rentabilidade_operacional_ativos", "margem_operacional", "giro_ativo"]].dropna()
    rentabilidade = tripla["rentabilidade_operacional_ativos"].to_numpy(dtype=float)
    produto = (tripla["margem_operacional"] * tripla["giro_ativo"]).to_numpy(dtype=float)
    return {
        "OBSERVACOES_TRIPLA": len(tripla), "EMISSORES_TRIPLA": tripla["CD_CVM"].nunique(),
        "FORA_DA_TOLERANCIA": int((~np.isclose(rentabilidade, produto, rtol=1e-10, atol=1e-12)).sum()),
        "ERRO_ABSOLUTO_MAXIMO": float(np.abs(rentabilidade - produto).max()) if len(tripla) else np.nan,
    }


def diagnosticar_indicadores(tabela: pd.DataFrame, *, minimo_correlacao: int = 10) -> dict[str, pd.DataFrame]:
    """Calcula contagens, distribuição e correlação sem pontuar emissores."""
    if minimo_correlacao < 2:
        raise ValueError("O mínimo para correlação deve ser de pelo menos dois emissores e pares.")
    ampla = matriz_indicadores(tabela)
    cobertura, perfis, distribuicoes, correlacoes, identidades = [], [], [], [], []
    for grupo, recorte in _por_recorte(ampla):
        codigos = recorte["CD_CVM"].to_numpy()
        matriz = recorte[list(INDICADORES)].to_numpy(dtype=float, na_value=np.nan)
        validas = np.isfinite(matriz)
        base = {**grupo, "OBSERVACOES": len(recorte), "EMISSORES": _contagem_emissores(codigos)}
        identidades.append({**base, **_identidade_ativos(recorte)})
        total_quality = recorte[INDICADORES_QUALITY].notna().sum(axis=1).to_numpy()
        total_distress = recorte[INDICADORES_DISTRESS].notna().sum(axis=1).to_numpy()
        for quality, distress in np.unique(np.column_stack([total_quality, total_distress]), axis=0):
            perfil = (total_quality == quality) & (total_distress == distress)
            perfis.append({
                **base, "N_QUALITY": quality, "N_DISTRESS": distress,
                "OBSERVACOES_PERFIL": int(perfil.sum()), "EMISSORES_PERFIL": _contagem_emissores(codigos[perfil]),
            })
        for coluna, indicador in enumerate(INDICADORES):
            mascara = validas[:, coluna]
            comum = {
                **base, "INDICADOR": indicador, "EIXO": PROTOTIPOS[indicador].eixo,
                "OBSERVACOES_VALIDAS": int(mascara.sum()), "EMISSORES_VALIDOS": _contagem_emissores(codigos[mascara]),
            }
            cobertura.append(comum)
            distribuicoes.append({**comum, **_quantis(matriz[mascara, coluna])})
        for primeiro, segundo in combinations(range(len(INDICADORES)), 2):
            mascara = validas[:, primeiro] & validas[:, segundo]
            emissores_pareados = _contagem_emissores(codigos[mascara])
            correlacoes.append({
                **base, "INDICADOR_X": INDICADORES[primeiro], "INDICADOR_Y": INDICADORES[segundo],
                "OBSERVACOES_PAREADAS": int(mascara.sum()), "EMISSORES_PAREADOS": emissores_pareados,
                **_correlacao(matriz[mascara][:, [primeiro, segundo]], emissores_pareados, minimo_correlacao),
            })

    estados = tabela[[*CHAVE_OBSERVACAO, *COLUNAS_SETOR, "INDICADOR", "SITUACAO"]].copy()
    estados["TIPO_DENOMINADOR"] = [
        _tipo_denominador(*linha)
        for linha in tabela[["INDICADOR", "SITUACAO", "FONTES"]].itertuples(index=False, name=None)
    ]
    situacoes, denominadores = [], []
    for nivel, chaves in RECORTES.items():
        for categoria, destino in (("SITUACAO", situacoes), ("TIPO_DENOMINADOR", denominadores)):
            contagens = (
                estados.groupby([*chaves, "INDICADOR", categoria], dropna=False, observed=True)
                .agg(OBSERVACOES=("CD_CVM", "size"), EMISSORES=("CD_CVM", "nunique"))
                .reset_index()
            )
            contagens["NIVEL"] = nivel
            destino.append(contagens)
    return {
        "cobertura_indicadores": pd.DataFrame(cobertura), "cobertura_conjunta": pd.DataFrame(perfis),
        "distribuicoes": pd.DataFrame(distribuicoes), "correlacoes": pd.DataFrame(correlacoes),
        "identidade_margem_giro": pd.DataFrame(identidades),
        "situacoes": pd.concat(situacoes, ignore_index=True),
        "denominadores": pd.concat(denominadores, ignore_index=True),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera diagnósticos agregados da Sprint 03A.")
    parser.add_argument("--painel", type=Path, default=Path("data/processed/sprint02"))
    parser.add_argument("--saida", type=Path, default=Path("outputs/sprint03a-diagnosticos"))
    parser.add_argument("--minimo-correlacao", type=int, default=10)
    args = parser.parse_args()
    try:
        tabelas = diagnosticar_indicadores(carregar_indicadores(args.painel), minimo_correlacao=args.minimo_correlacao)
        args.saida.mkdir(parents=True, exist_ok=True)
        for nome, tabela in tabelas.items():
            tabela.to_csv(args.saida / f"{nome}.csv", index=False)
    except (OSError, KeyError, ValueError) as erro:
        parser.exit(1, f"Falha no diagnóstico: {erro}\n")
    print(args.saida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
