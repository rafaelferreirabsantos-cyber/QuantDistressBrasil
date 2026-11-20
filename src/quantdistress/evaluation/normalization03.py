"""Comparação agregada de normalizações univariadas no painel descritivo."""

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

from .diagnostics03 import carregar_indicadores
from .references03 import selecionar_ultima_referencia

COLUNAS = [
    "ANO_ARQUIVO", "DT_REFER", "CD_CVM", "ESCOPO", "SETOR_FCA", "GRUPO_SETORIAL",
    "INDICADOR", "SITUACAO", "VALOR",
]
COORTE = ["ANO_ARQUIVO", "ESCOPO", "INDICADOR"]
METODOS = ("percentil", "z", "robusto")


def _selecionar_ano_emissor(painel: pd.DataFrame) -> pd.DataFrame:
    unicos = painel.loc[selecionar_ultima_referencia(painel, por_indicador=True)]
    valores = unicos["VALOR"].to_numpy(dtype=float, na_value=np.nan)
    mask = (
        unicos["GRUPO_SETORIAL"].eq("nao_financeira")
        & unicos["ESCOPO"].isin(["con", "ind"])
        & unicos["SITUACAO"].eq("valido")
        & np.isfinite(valores)
    )
    return unicos.loc[mask].reset_index(drop=True)


def _referencia_util(valores: np.ndarray, min_pares: int) -> bool:
    return valores.size >= min_pares and valores.max() > valores.min()


def _normalizar(alvos: np.ndarray, calibracao: np.ndarray, metodo: str, min_pares: int) -> np.ndarray:
    pontos = np.full(alvos.shape, np.nan, dtype=float)
    ref = calibracao[np.isfinite(calibracao)]
    if not _referencia_util(ref, min_pares):
        return pontos
    validos = np.isfinite(alvos)
    x = alvos[validos]
    if metodo == "percentil":
        ordenados = np.sort(ref)
        anteriores = np.searchsorted(ordenados, x, side="left")
        ate_alvo = np.searchsorted(ordenados, x, side="right")
        pontos[validos] = 50.0 * (anteriores + ate_alvo) / ref.size
        return pontos

    if metodo == "z":
        centro, escala = ref.mean(), ref.std(ddof=0)
    else:
        centro = np.median(ref)
        escala = 1.4826 * np.median(np.abs(ref - centro))
        if escala == 0:
            q1, q3 = np.quantile(ref, [0.25, 0.75])
            escala = (q3 - q1) / 1.349
    if np.isfinite(escala) and escala > 0:
        padronizados = (x - centro) / escala
        # A função normal apenas expressa os z em pontos para a comparação.
        pontos[validos] = np.fromiter(
            (50.0 * math.erfc(-z / math.sqrt(2.0)) for z in padronizados),
            dtype=float,
            count=x.size,
        )
    return pontos


def _perturbar_cauda(ref: np.ndarray) -> np.ndarray:
    estressada = ref.copy()
    if len(ref):
        maior = ref.argmax()
        estressada[maior] += 100.0 * np.ptp(ref)
    return estressada


def _comparar(atual: np.ndarray, outra: np.ndarray, cenario: str) -> dict:
    comparaveis = np.isfinite(atual) & np.isfinite(outra)
    diferenca = np.abs(atual[comparaveis] - outra[comparaveis])
    return {
        f"N_COMPARAVEIS_{cenario}": len(diferenca),
        f"MEDIANA_ABS_{cenario}": np.median(diferenca) if len(diferenca) else np.nan,
        f"P90_ABS_{cenario}": np.quantile(diferenca, 0.9) if len(diferenca) else np.nan,
        f"N_DIFERENCA_MAIOR_10_{cenario}": np.count_nonzero(diferenca > 10),
    }


def _referencia_setorial(
    alvos: pd.DataFrame, ref: pd.DataFrame, metodo: str, minimo: int, amplo: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    resultado = amplo.copy()
    tem_setor = np.zeros(len(alvos), dtype=bool)
    referencias = {
        setor: grupo["VALOR"].to_numpy(dtype=float)
        for setor, grupo in ref.groupby("SETOR_FCA", dropna=True)
    }
    for setor, posicoes in alvos.groupby("SETOR_FCA", dropna=True).indices.items():
        if setor not in referencias or not _referencia_util(referencias[setor], minimo):
            continue
        x = alvos.iloc[posicoes]["VALOR"].to_numpy(dtype=float)
        local = _normalizar(x, referencias[setor], metodo, minimo)
        validos = np.isfinite(local)
        resultado[posicoes[validos]] = local[validos]
        tem_setor[posicoes[validos]] = True
    return resultado, tem_setor


def experimentar_normalizacao(painel: pd.DataFrame, *, min_pares: int = 30) -> pd.DataFrame:
    """Resume perturbações e mudanças de referência por ano, indicador e escopo."""
    if min_pares < 2:
        raise ValueError("A referência deve exigir pelo menos dois pares.")
    validos = _selecionar_ano_emissor(painel)
    coortes = dict(tuple(validos.groupby(COORTE, sort=True)))
    vazio = validos.iloc[:0]
    resumo = []
    for (ano, escopo, indicador), alvos in coortes.items():
        anterior = coortes.get((ano - 1, escopo, indicador), vazio)
        x = alvos["VALOR"].to_numpy(dtype=float)
        ref_anterior = anterior["VALOR"].to_numpy(dtype=float)
        contaminada = _perturbar_cauda(x)
        percentil = _normalizar(x, x, "percentil", min_pares)
        for metodo in METODOS:
            ampla = _normalizar(x, x, metodo, min_pares)
            lag = _normalizar(x, ref_anterior, metodo, min_pares)
            extrema = _normalizar(x, contaminada, metodo, min_pares)
            setor, local = _referencia_setorial(alvos, alvos, metodo, min_pares, ampla)
            setor_anterior, local_anterior = _referencia_setorial(alvos, anterior, metodo, min_pares, lag)
            resumo.append({
                "ANO_ARQUIVO": ano, "ESCOPO": escopo, "INDICADOR": indicador, "METODO": metodo,
                "MIN_PARES": min_pares, "N_ALVOS": len(alvos), "N_REF_ANO_ANTERIOR": len(anterior),
                "N_NORMALIZACAO_AMPLA": np.count_nonzero(np.isfinite(ampla)),
                "N_NORMALIZACAO_SETORIAL": np.count_nonzero(local),
                "N_FALLBACK_AMPLA": np.count_nonzero(np.isfinite(setor) & ~local),
                "N_NORMALIZACAO_SETORIAL_ANO_ANTERIOR": np.count_nonzero(local_anterior),
                "N_FALLBACK_AMPLA_ANO_ANTERIOR": np.count_nonzero(np.isfinite(setor_anterior) & ~local_anterior),
                **_comparar(ampla, percentil, "METODO_VS_PERCENTIL"),
                **_comparar(ampla, extrema, "CAUDA"),
                **_comparar(ampla, lag, "ANO_ANTERIOR"),
                **_comparar(ampla[local], setor[local], "SETOR_VS_AMPLA"),
                **_comparar(setor, setor_anterior, "SETOR_ANO_ANTERIOR"),
            })
    return pd.DataFrame(resumo)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--painel", type=Path, default=Path("data/processed/sprint02"))
    parser.add_argument("--saida", type=Path, default=Path("outputs/sprint03a/normalizacao_experimentos.csv"))
    parser.add_argument("--min-pares", type=int, default=30)
    args = parser.parse_args()

    painel = carregar_indicadores(args.painel)[COLUNAS]
    resumo = experimentar_normalizacao(painel, min_pares=args.min_pares)
    if resumo.empty:
        parser.error("O painel não tem observações aptas para o experimento.")
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    resumo.assign(MODO_TEMPORAL="descritivo_revisado", PROTOCOLO_REF="inclusivo_legado").to_csv(args.saida, index=False)
    print(f"{len(resumo)} resultados agregados em {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
