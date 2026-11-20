"""Matriz descritiva dos eixos simultâneos, com contagens por faixa e escopo."""

from pathlib import Path

import numpy as np
import pandas as pd

from .sensitivity03b import EIXOS, MODO

LIMITES = np.arange(0, 101, 10)
ESCOPOS = {"con": "Consolidado", "ind": "Individual sem consolidado na fonte"}


def contar_matriz(scores: pd.DataFrame) -> pd.DataFrame:
    if not scores["MODO_TEMPORAL"].eq(MODO).fillna(False).all():
        raise ValueError("A matriz exige o modo descritivo_revisado.")
    ambos = scores.dropna(subset=list(EIXOS))
    registros = []
    anos = sorted(scores["ANO_ARQUIVO"].unique())
    for escopo in ESCOPOS:
        amostra = ambos.loc[ambos["ESCOPO"].eq(escopo)]
        for ano in [None, *anos]:
            grupo = amostra if ano is None else amostra.loc[amostra["ANO_ARQUIVO"].eq(ano)]
            q, d = (grupo[eixo].to_numpy(dtype=float) for eixo in EIXOS)
            if ((q < -1e-12) | (q > 100 + 1e-12) | ~np.isfinite(q)).any() or (
                (d < -1e-12) | (d > 100 + 1e-12) | ~np.isfinite(d)
            ).any():
                raise ValueError("A matriz exige scores finitos entre 0 e 100.")
            grade = np.histogram2d(q.clip(0, 100), d.clip(0, 100), bins=(LIMITES, LIMITES))[0]
            registros.extend({
                "ESCOPO": escopo, "ANO_ARQUIVO": ano,
                "QUALITY_DE": i * 10, "QUALITY_ATE": (i + 1) * 10,
                "DISTRESS_DE": j * 10, "DISTRESS_ATE": (j + 1) * 10,
                "OBSERVACOES": int(total), "MODO_TEMPORAL": MODO,
            } for (i, j), total in np.ndenumerate(grade))
    return pd.DataFrame(registros).astype({"ANO_ARQUIVO": "Int64"})


def renderizar_matriz(matriz: pd.DataFrame, destino: Path, anos: tuple[int, int]) -> None:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    from matplotlib.ticker import MaxNLocator

    fundo, texto, fraco, destaque = "#f7f8f5", "#173044", "#425b69", "#177f78"
    figura = Figure(figsize=(11, 6.5), dpi=160, facecolor=fundo)
    FigureCanvasAgg(figura)
    eixos = figura.subplots(1, 2)
    figura.subplots_adjust(left=.085, right=.876, top=.767, bottom=.19, wspace=.25)
    totals = matriz.loc[matriz["ANO_ARQUIVO"].isna()]
    maximo = max(1, int(totals["OBSERVACOES"].max()))
    for eixo, (escopo, rotulo) in zip(eixos, ESCOPOS.items(), strict=True):
        estrato = totals.loc[totals["ESCOPO"].eq(escopo)]
        grade = estrato.pivot(index="DISTRESS_DE", columns="QUALITY_DE", values="OBSERVACOES").to_numpy()
        imagem = eixo.imshow(grade, origin="lower", extent=(0, 100, 0, 100), cmap="PuBuGn", vmin=0, vmax=maximo)
        n = f"{grade.sum():,}".replace(",", ".")
        eixo.set_title(f"{rotulo}  ·  n = {n}", fontsize=11, fontweight="bold", color=texto, pad=10)
        for (i, j), valor in np.ndenumerate(grade):
            if valor:
                cor = "white" if valor >= .58 * maximo else texto
                eixo.text(j * 10 + 5, i * 10 + 5, str(valor), ha="center", va="center", fontsize=7, color=cor)
        eixo.axhline(50, color=destaque, linewidth=1.0, dashes=(4, 3))
        eixo.axvline(50, color=destaque, linewidth=1.0, dashes=(4, 3))
        eixo.set(xticks=[0, 20, 40, 60, 80, 100], yticks=[0, 20, 40, 60, 80, 100])
        eixo.tick_params(length=0, labelsize=9, colors=fraco)
        eixo.set_xlabel("Quality Score", fontsize=10, labelpad=8, color=texto)
        for borda in eixo.spines.values():
            borda.set_visible(False)
    eixos[0].set_ylabel("Financial Distress Score", fontsize=10, labelpad=9, color=texto)
    barra = figura.colorbar(imagem, cax=figura.add_axes([.91, .26, .017, .42]), ticks=MaxNLocator(5, integer=True))
    barra.set_label("Observações por célula", color=fraco, fontsize=9)
    barra.ax.tick_params(labelsize=8, length=0, colors=fraco)
    barra.outline.set_visible(False)
    figura.text(.085, .924, "QUANTDISTRESS BRASIL  /  IMPACTUFSCAR", color=destaque, fontsize=9, weight="bold")
    figura.text(.085, .866, "Matriz Quality × Financial Distress", color=texto, fontsize=22, weight="bold")
    periodo = str(anos[0]) if anos[0] == anos[1] else f"{anos[0]}–{anos[1]}"
    figura.text(.085, .818, f"DFP CVM · {periodo} · Setor FCA exato · 30 pares · Dados revisados", color=fraco, fontsize=10)
    figura.text(.085, .105, "Cada célula conta observações de emissor e exercício com os dois eixos calculados.", color=fraco, fontsize=9)
    figura.text(.085, .069, "Linhas em 50 são uma convenção exploratória. As referências permanecem separadas por ano, setor e escopo.", color=fraco, fontsize=8.5)
    figura.savefig(destino, facecolor=fundo)
