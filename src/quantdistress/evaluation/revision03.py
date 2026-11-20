"""Revisão descritiva de referências, sensibilidade e suporte na Sprint 03A."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from quantdistress.data._snapshot import gravar_json, ler_json, sha256
from quantdistress.features.indicators import PROTOTIPOS

from .feasibility03 import D_NUCLEO, Q_NUCLEO
from .references03 import (
    AmostraReferencia,
    agrupar_referencias,
    percentil_ponto_medio,
    selecionar_ultima_referencia,
)

MODO = "descritivo_revisado"
CENTRAIS = (*Q_NUCLEO, *D_NUCLEO)
COORTE = ["ANO_ARQUIVO", "ESCOPO", "SETOR_FCA", "INDICADOR"]
AMPLO = ["ANO_ARQUIVO", "ESCOPO", "INDICADOR"]
UNIDADE = ["ANO_ARQUIVO", "ESCOPO", "SETOR_FCA", "CD_CVM"]
MACROSETORES = {
    "utilidades": ("Energia Elétrica", "Saneamento, Serv. Água e Gás"),
    "transformacao": (
        "Metalurgia e Siderurgia", "Máquinas, Equipamentos, Veículos e Peças", "Petroquímicos e Borracha",
    ),
}
ROTULO_MACRO = {setor: macro for macro, setores in MACROSETORES.items() for setor in setores}
VAZIA = pd.Series(dtype=float)
COLUNAS = [*COORTE, "CD_CVM", "DT_REFER", "GRUPO_SETORIAL", "VALOR", "SITUACAO", "ID_DOC", "FONTES",
           "SITUACAO_ENTREGA_DFP", "DT_DIVULGACAO", "MODO_TEMPORAL", "SHA256_DFP"]


def carregar_painel(painel: Path) -> pd.DataFrame:
    manifesto = ler_json(painel / "manifesto.json")
    if manifesto["modo_temporal"] != MODO:
        raise ValueError("Esperado o painel descritivo revisado da Sprint 02.")
    anos = manifesto["anos"]
    if not anos or len({entrada["ano"] for entrada in anos}) != len(anos):
        raise ValueError("O manifesto deve listar partições anuais distintas.")
    quadros = []
    for entrada in anos:
        ano = entrada["ano"]
        tabela = pd.read_parquet(painel / str(ano) / "indicadores.parquet", columns=COLUNAS)
        esperadas = tabela["ANO_ARQUIVO"].eq(ano) & tabela["MODO_TEMPORAL"].eq(MODO)
        esperadas &= tabela["SHA256_DFP"].eq(entrada["fonte_dfp"]["sha256"])
        if len(tabela) != entrada["observacoes_indicadores"] or not esperadas.fillna(False).all():
            raise ValueError(f"Partição incompatível com o manifesto: {ano}.")
        quadros.append(tabela)
    base = pd.concat(quadros, ignore_index=True)
    base = base.loc[base["INDICADOR"].isin(CENTRAIS)]
    escolhidas = selecionar_ultima_referencia(base, por_indicador=True)
    return base.loc[escolhidas & base["GRUPO_SETORIAL"].eq("nao_financeira")
                    & base["SITUACAO_ENTREGA_DFP"].eq("unica")].copy()


def diagnostico_contabil(situacao: str, fontes: str, documento: str, indicador: str) -> str:
    """Distingue rastreabilidade automática, lacunas e o primeiro bloqueio no painel."""
    if situacao != "valido":
        return str(situacao)
    try:
        insumos = json.loads(fontes)
        esperado = [nome for nome, _ in PROTOTIPOS[indicador].insumos]
        rastreavel = pd.notna(documento) and [f["CONCEITO"] for f in insumos] == esperado and all(
            f["ID_DOC"] == documento and bool(f["ARQUIVO_ORIGEM"]) and f["LINHA_ORIGEM"] > 0
            for f in insumos
        )
    except (TypeError, KeyError, ValueError):
        rastreavel = False
    return "linhagem_validada_automaticamente" if rastreavel else "linhagem_incompleta"


def _amostra(serie: pd.Series, n: int, chave: tuple) -> pd.Series:
    ids = sorted(serie.index, key=lambda codigo: hashlib.sha256(f"{chave!r}|{codigo}".encode()).digest())
    return serie.loc[ids[:n]]


def cenarios_referencia(ref: pd.Series, anterior: pd.Series, externos: pd.Series, ids_atuais, chave: tuple) -> dict:
    """Perturba composição ou valores usando uma seleção de códigos independente dos valores."""
    n = len(ref) // 5
    novos = _amostra(anterior.loc[~anterior.index.isin(ids_atuais)], n, (*chave, "entrada"))
    saida = _amostra(ref, n, (*chave, "saida"))
    trocas = _amostra(externos.loc[~externos.index.isin(ids_atuais)], n, (*chave, "composicao"))
    fora = _amostra(ref, len(trocas), (*chave, "substituir"))
    resultados = {
        "entrada": (pd.concat([ref, novos]), novos.index) if len(novos) else None,
        "saida": (ref.drop(saida.index), saida.index) if n else None,
        "composicao_macro": (pd.concat([ref.drop(fora.index), trocas]), fora.index.append(trocas.index)) if len(trocas) else None,
        "ano_anterior": (anterior, None) if len(anterior) else None,
        "valores_intermediarios": None,
        "cauda": None,
    }
    if ref.nunique() > 1:
        q25, q40, q60, q75 = ref.quantile([.25, .40, .60, .75])
        alterados = ref.between(q40, q60) & (q75 > q25)
        if alterados.any():
            resultados["valores_intermediarios"] = (ref.where(~alterados, ref + (q75 - q25) / 2), ref.index[alterados])
        cauda = ref.copy()
        maior = cauda.idxmax()
        cauda.loc[maior] += 100 * (ref.max() - ref.min())
        resultados["cauda"] = (cauda, pd.Index([maior]))
    return resultados


def _contagens_nucleos(suporte: pd.DataFrame) -> pd.DataFrame:
    opcoes = {
        "setor_exato": suporte["EXATO"],
        **{macro: suporte["EXATO"] | (suporte["MACROSETOR"].eq(macro) & suporte["MACRO_OK"])
           for macro in MACROSETORES},
        "macros_candidatos": suporte["EXATO"] | suporte["MACRO_OK"],
        "amplo_exploratorio": suporte["EXATO"] | suporte["AMPLO_OK"],
    }
    resumos = []
    base = suporte.pivot(index=UNIDADE, columns="INDICADOR", values="EXATO").reindex(columns=CENTRAIS).eq(True)
    q_base, d_base = base[list(Q_NUCLEO)].all(axis=1), base[list(D_NUCLEO)].all(axis=1)
    for opcao, flag in opcoes.items():
        unidade = suporte.assign(ATENDE=flag).pivot(index=UNIDADE, columns="INDICADOR", values="ATENDE")
        unidade = unidade.reindex(columns=CENTRAIS).eq(True)
        q, d = unidade[list(Q_NUCLEO)].all(axis=1), unidade[list(D_NUCLEO)].all(axis=1)
        unidade = unidade.assign(
            Q=q, D=d, AMBOS=q & d, Q_RECUPERADAS=q & ~q_base, D_RECUPERADAS=d & ~d_base,
            RECUPERADAS=q & d & ~(q_base & d_base),
        ).reset_index()
        unidade["CVM_AMBOS"] = unidade["CD_CVM"].where(unidade["AMBOS"])
        unidade["CVM_RECUPERADAS"] = unidade["CD_CVM"].where(unidade["RECUPERADAS"])
        for nome, chaves in (
            ("periodo_escopo", ["ESCOPO"]), ("ano_escopo", ["ANO_ARQUIVO", "ESCOPO"]),
            ("periodo_setor", ["ESCOPO", "SETOR_FCA"]), ("ano_setor", UNIDADE[:-1]),
        ):
            resumos.append(unidade.groupby(chaves, dropna=False).agg(
                TOTAL=("CD_CVM", "size"), EMISSORES=("CD_CVM", "nunique"),
                Q=("Q", "sum"), D=("D", "sum"), AMBOS=("AMBOS", "sum"),
                Q_RECUPERADAS=("Q_RECUPERADAS", "sum"), D_RECUPERADAS=("D_RECUPERADAS", "sum"),
                RECUPERADAS=("RECUPERADAS", "sum"), EMISSORES_AMBOS=("CVM_AMBOS", "nunique"),
                EMISSORES_RECUPERADOS=("CVM_RECUPERADAS", "nunique"),
            ).reset_index().assign(REFERENCIA=opcao, NIVEL=nome))
    return pd.concat(resumos, ignore_index=True)


def _resumir_robustez(casos: pd.DataFrame) -> pd.DataFrame:
    niveis = [
        ("periodo_escopo", ["ESCOPO"]), ("ano_escopo", ["ANO_ARQUIVO", "ESCOPO"]),
        ("ano_setor_indicador", COORTE),
    ]
    return pd.concat([
        casos.groupby([*chaves, "CENARIO"], dropna=False).agg(
            ALVOS=("CD_CVM", "size"), EMISSORES=("CD_CVM", "nunique"),
            COM_BASE=("BASE", "sum"), COM_CENARIO=("VARIANTE", "sum"),
            PERDAS=("PERDA", "sum"), GANHOS=("GANHO", "sum"),
            COMPARAVEIS=("DELTA_PP", "count"), ACIMA_10_PP=("ACIMA_10_PP", "sum"),
            MEDIANA_DELTA_PP=("DELTA_PP", "median"), P90_DELTA_PP=("DELTA_PP", lambda x: x.quantile(.9)),
            MAX_DELTA_PP=("DELTA_PP", "max"), MEDIANA_PARES_AFETADOS=("PARES_AFETADOS", "median"),
        ).reset_index().assign(NIVEL=nivel)
        for nivel, chaves in niveis
    ], ignore_index=True)


def experimentar_revisao(alvos: pd.DataFrame, min_pares: int = 30) -> dict[str, pd.DataFrame]:
    """Produz exclusivamente agregados da revisão e mantém a disponibilidade e os controles separados."""
    if min_pares < 2 or alvos.empty:
        raise ValueError("O experimento exige observações e pelo menos dois pares.")
    colunas_contabeis = ["SITUACAO", "FONTES", "ID_DOC", "INDICADOR"]
    status_contabeis = [diagnostico_contabil(*linha) for linha in alvos[colunas_contabeis].itertuples(index=False, name=None)]
    valor_disponivel = alvos["SITUACAO"].eq("valido") & np.isfinite(alvos["VALOR"].to_numpy(dtype=float, na_value=np.nan))
    doc = alvos.assign(MACROSETOR=alvos["SETOR_FCA"].map(ROTULO_MACRO), A_CONTABIL=status_contabeis, DISPONIVEL=valor_disponivel)
    validos = doc.loc[doc["DISPONIVEL"] & doc["A_CONTABIL"].eq("linhagem_validada_automaticamente")]
    exatos = agrupar_referencias(validos, COORTE)
    amplos = agrupar_referencias(validos, AMPLO)
    macros = agrupar_referencias(validos, [*AMPLO, "MACROSETOR"])
    painel_suporte, robustez = [], []
    for chave, grupo in doc.groupby(COORTE):
        ano, escopo, setor, indicador = chave
        ref = exatos.get(chave, VAZIA)
        anterior = exatos.get((ano - 1, escopo, setor, indicador), VAZIA)
        macro_nome = ROTULO_MACRO.get(setor, "sem_macro_candidato")
        macro = macros.get((ano, escopo, indicador, macro_nome), VAZIA)
        amplo = amplos.get((ano, escopo, indicador), VAZIA)
        ids_atuais = pd.Index(grupo["CD_CVM"])
        mudancas = {
            nome: (AmostraReferencia(par[0]), par[1])
            for nome, par in cenarios_referencia(ref, anterior, macro, ids_atuais, chave).items() if par is not None
        }
        referencia_exata, referencia_macro, referencia_ampla = map(AmostraReferencia, (ref, macro, amplo))
        inclusiva = referencia_exata.preparar(min_pares=min_pares)
        for alvo in grupo.itertuples(index=False):
            cvm = alvo.CD_CVM
            valor = alvo.VALOR
            config = {"min_pares": min_pares, "emissor_excluido": cvm}
            exata = referencia_exata.preparar(**config)
            apto = alvo.DISPONIVEL and alvo.A_CONTABIL == "linhagem_validada_automaticamente"
            marco = referencia_macro.preparar(**config) if len(macro) else None
            fundo = referencia_ampla.preparar(**config)
            painel_suporte.append({
                **dict(zip(COORTE, chave, strict=True)), "CD_CVM": cvm, "DISPONIVEL": alvo.DISPONIVEL,
                "A_CONTABIL": alvo.A_CONTABIL, "DATA_DIVULGACAO": "ausente" if pd.isna(alvo.DT_DIVULGACAO) else "informada_sem_verificacao",
                "S_ESTATISTICO": exata.situacao, "N_PARES": exata.n_pares, "MAIOR_EMPATE": exata.maior_empate,
                "MASSA_MAIOR_EMPATE": exata.maior_empate / exata.n_pares if exata.n_pares else np.nan,
                "EXATO": apto and exata.situacao == "utilizavel", "MACROSETOR": macro_nome,
                "MACRO_OK": apto and marco is not None and marco.situacao == "utilizavel",
                "AMPLO_OK": apto and fundo.situacao == "utilizavel",
            })
            if not apto:
                continue
            base = percentil_ponto_medio(valor, exata)
            pontos = {
                "proprio_emissor_incluido": (percentil_ponto_medio(valor, inclusiva), int(cvm in ref.index)),
                "amplo_exploratorio": (percentil_ponto_medio(valor, fundo), np.nan),
            }
            if macro_nome in MACROSETORES:
                pontos["macro_candidato"] = (percentil_ponto_medio(valor, marco), np.nan)
            for nome, (fonte, afetados) in mudancas.items():
                n = np.nan if afetados is None else len(afetados) - int(cvm in afetados)
                if n == 0:
                    continue
                pontos[nome] = (percentil_ponto_medio(valor, fonte.preparar(**config)), n)
            if exata.situacao == "utilizavel":
                q1, q3 = np.quantile(exata.valores, [.25, .75])
                if q3 > q1:
                    for sinal, nome in ((-1, "indicador_menos_01_iqr"), (1, "indicador_mais_01_iqr")):
                        pontos[nome] = (percentil_ponto_medio(valor + sinal * (q3 - q1) / 10, exata), 0)
            for nome, (ponto, n) in pontos.items():
                ambos = np.isfinite(base) and np.isfinite(ponto)
                delta = abs(ponto - base) if ambos else np.nan
                robustez.append({
                    **dict(zip(COORTE, chave, strict=True)), "CD_CVM": cvm, "CENARIO": nome,
                    "BASE": np.isfinite(base), "VARIANTE": np.isfinite(ponto),
                    "PERDA": np.isfinite(base) and not np.isfinite(ponto), "GANHO": np.isfinite(ponto) and not np.isfinite(base),
                    "DELTA_PP": delta, "ACIMA_10_PP": delta > 10 + 1e-12, "PARES_AFETADOS": n,
                })
    suporte = pd.DataFrame(painel_suporte)
    chaves = [*COORTE, "DISPONIVEL", "A_CONTABIL", "DATA_DIVULGACAO", "S_ESTATISTICO"]
    resumo = suporte.groupby(chaves, dropna=False).agg(
        OBSERVACOES=("CD_CVM", "size"), EMISSORES=("CD_CVM", "nunique"),
        MEDIANA_PARES=("N_PARES", "median"), MENOR_N=("N_PARES", "min"),
        MAIOR_N=("N_PARES", "max"), MAIOR_EMPATE=("MAIOR_EMPATE", "max"),
        MAIOR_MASSA_EMPATE=("MASSA_MAIOR_EMPATE", "max"),
    ).reset_index().assign(ELEGIBILIDADE_TEMPORAL="bloqueada_sem_evidencia")
    return {
        "suporte_componentes": resumo,
        "cobertura_macrosetores": _contagens_nucleos(suporte),
        "robustez_percentil": _resumir_robustez(pd.DataFrame(robustez, columns=[
            *COORTE, "CD_CVM", "CENARIO", "BASE", "VARIANTE", "PERDA", "GANHO", "DELTA_PP",
            "ACIMA_10_PP", "PARES_AFETADOS",
        ])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--painel", type=Path, default=Path("data/processed/sprint02"))
    parser.add_argument("--saida", type=Path, default=Path("outputs/sprint03a-revisao"))
    parser.add_argument("--min-pares", type=int, default=30)
    args = parser.parse_args()
    tabelas = experimentar_revisao(carregar_painel(args.painel), args.min_pares)
    args.saida.mkdir(parents=True, exist_ok=True)
    for nome, tabela in tabelas.items():
        tabela.assign(MODO_TEMPORAL=MODO, MIN_PARES=args.min_pares).to_csv(args.saida / f"{nome}.csv", index=False)
    gravar_json(args.saida / "manifesto.json", {
        "modo_temporal": MODO, "sha256_manifesto_painel": sha256(args.painel / "manifesto.json"),
        "min_pares": args.min_pares, "tabelas": {nome: len(tabela) for nome, tabela in tabelas.items()},
    })
    print(args.saida.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
