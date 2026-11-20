"""Indicadores contábeis descritivos da DFP, com critérios e linhagem por cálculo."""

import json
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, InvalidOperation, localcontext

import pandas as pd

from quantdistress.data.dfp import CHAVE_ENTREGA, FATORES_ESCALA

from ._conceitos import CONCEITOS

CHAVE_PAINEL = (*CHAVE_ENTREGA, "ESCOPO")
ATUAL = "ÚLTIMO"
ANTERIOR = "PENÚLTIMO"
DIA = timedelta(days=1)
FAMILIAS_SALDO = {"BPA", "BPP"}


class _FalhaIndicador(ValueError):
    def __init__(self, situacao: str, detalhe: str):
        super().__init__(detalhe)
        self.situacao = situacao


@dataclass(frozen=True)
class _Insumo:
    valor: Decimal
    inicio: pd.Timestamp
    fim: pd.Timestamp
    fonte: dict


def _razao(numerador: Decimal, denominador: Decimal) -> Decimal:
    if denominador <= 0:
        raise _FalhaIndicador("denominador_invalido", "O denominador deve ser positivo.")
    return numerador / denominador


def _saldos(numerador: _Insumo, denominador: _Insumo) -> Decimal:
    return _razao(numerador.valor, denominador.valor)


def _fluxos(numerador: _Insumo, denominador: _Insumo) -> Decimal:
    if (numerador.inicio, numerador.fim) != (denominador.inicio, denominador.fim):
        raise _FalhaIndicador("periodo_incompativel", "Os intervalos dos fluxos divergem.")
    return _saldos(numerador, denominador)


def _sobre_ativo_medio(fluxo: _Insumo, final: _Insumo, inicial: _Insumo) -> Decimal:
    if inicial.fim + DIA != fluxo.inicio or final.fim != fluxo.fim:
        raise _FalhaIndicador(
            "periodo_incompativel", "Os saldos de ativo não delimitam o intervalo do fluxo.",
        )
    return _razao(fluxo.valor, (inicial.valor + final.valor) / 2)


def _giro_ativo(receita: _Insumo, final: _Insumo, inicial: _Insumo) -> Decimal:
    if receita.valor < 0:
        raise _FalhaIndicador("sinal_invalido", "A receita corrente deve ser não negativa.")
    return _sobre_ativo_medio(receita, final, inicial)


def _crescimento(atual: _Insumo, anterior: _Insumo) -> Decimal:
    if anterior.fim + DIA != atual.inicio:
        raise _FalhaIndicador("periodo_incompativel", "Os exercícios comparados devem ser contíguos.")
    if atual.valor < 0:
        raise _FalhaIndicador("sinal_invalido", "A receita corrente deve ser não negativa.")
    return _saldos(atual, anterior) - 1


def _financiamentos_sobre_ativo(curto: _Insumo, longo: _Insumo, ativo: _Insumo) -> Decimal:
    return _razao(curto.valor + longo.valor, ativo.valor)


@dataclass(frozen=True)
class _Prototipo:
    eixo: str
    insumos: tuple[tuple[str, str], ...]
    formula: Callable[..., Decimal]


RESULTADO = ("resultado_antes_financeiro_tributos", ATUAL)
RECEITA = ("receita_vendas_servicos", ATUAL)
ATIVO_FINAL = ("ativo_total", ATUAL)
ATIVO_INICIAL = ("ativo_total", ANTERIOR)
FINANCIAMENTOS_CURTOS = ("financiamentos_circulantes", ATUAL)

PROTOTIPOS = {
    "margem_operacional": _Prototipo("quality", (RESULTADO, RECEITA), _fluxos),
    "rentabilidade_operacional_ativos": _Prototipo(
        "quality", (RESULTADO, ATIVO_FINAL, ATIVO_INICIAL), _sobre_ativo_medio,
    ),
    "fluxo_caixa_operacional_sobre_receita": _Prototipo(
        "quality", (("fluxo_caixa_operacional", ATUAL), RECEITA), _fluxos,
    ),
    "giro_ativo": _Prototipo("quality", (RECEITA, ATIVO_FINAL, ATIVO_INICIAL), _giro_ativo),
    "crescimento_receita": _Prototipo(
        "quality", (RECEITA, ("receita_vendas_servicos", ANTERIOR)), _crescimento,
    ),
    "liquidez_corrente": _Prototipo(
        "distress", (("ativo_circulante", ATUAL), ("passivo_circulante", ATUAL)), _saldos,
    ),
    "patrimonio_liquido_sobre_ativo": _Prototipo(
        "distress", (("patrimonio_liquido", ATUAL), ATIVO_FINAL), _saldos,
    ),
    "financiamentos_reportados_sobre_ativo": _Prototipo(
        "distress",
        (FINANCIAMENTOS_CURTOS, ("financiamentos_nao_circulantes", ATUAL), ATIVO_FINAL),
        _financiamentos_sobre_ativo,
    ),
    "financiamentos_circulantes_sobre_caixa": _Prototipo(
        "distress", (FINANCIAMENTOS_CURTOS, ("caixa_equivalentes", ATUAL)), _saldos,
    ),
}


def _chave_observacao(linha) -> tuple:
    return tuple(getattr(linha, coluna) for coluna in CHAVE_PAINEL)


def _chave_conta(linha) -> tuple:
    return linha.FAMILIA, linha.CD_CONTA, linha.ORDEM_EXERC


def _contas_relevantes(fatos: pd.DataFrame) -> pd.DataFrame:
    pares = {(familia, regra.codigo) for regra in CONCEITOS.values() for familia in regra.familias}
    candidatas = pd.MultiIndex.from_frame(fatos[["FAMILIA", "CD_CONTA"]]).isin(pares)
    chaves_validas = fatos[list(CHAVE_PAINEL)].notna().all(axis=1)
    return fatos.loc[candidatas & chaves_validas & fatos["ORDEM_EXERC"].isin((ATUAL, ANTERIOR))]


def _rotulo(texto: str) -> str:
    return " ".join(texto.split()).casefold()


def _data_texto(data: pd.Timestamp) -> str | None:
    return None if pd.isna(data) else data.date().isoformat()


def _validar_periodo(linha, ordem: str, referencia: pd.Timestamp, nome: str) -> None:
    inicio, fim = linha.DT_INI_EXERC, linha.DT_FIM_EXERC
    fim_valido = pd.notna(fim) and (fim == referencia if ordem == ATUAL else fim < referencia)
    if linha.FAMILIA in FAMILIAS_SALDO:
        periodo_valido = pd.isna(inicio)
    else:
        periodo_valido = (
            pd.notna(inicio) and pd.notna(fim) and (fim - inicio).days + 1 in {365, 366}
        )
    if not fim_valido or not periodo_valido:
        raise _FalhaIndicador("periodo_incompativel", nome)


def _ler_insumo(registros: dict, conflitos: set, nome: str, ordem: str, observacao) -> _Insumo:
    regra = CONCEITOS[nome]
    alternativas = [(familia, regra.codigo, ordem) for familia in regra.familias]
    linhas = [linha for chave in alternativas for linha in registros.get(chave, ())]
    if conflitos.intersection(alternativas) or len(linhas) > 1:
        raise _FalhaIndicador("conflito_contabil", f"{nome} ({ordem})")
    if not linhas:
        raise _FalhaIndicador("conta_ausente", f"{nome} ({ordem})")

    linha, = linhas
    if (
        pd.isna(linha.SITUACAO_VINCULO) or linha.SITUACAO_VINCULO != "unico"
        or pd.isna(linha.ID_DOC) or pd.isna(linha.ARQUIVO_ORIGEM) or pd.isna(linha.LINHA_ORIGEM)
    ):
        raise _FalhaIndicador("vinculo_invalido", nome)
    rotulos = {_rotulo(rotulo) for rotulo in regra.rotulos_do_escopo(observacao.ESCOPO)}
    if (
        pd.isna(linha.ST_CONTA_FIXA) or linha.ST_CONTA_FIXA != "S"
        or pd.isna(linha.DS_CONTA) or _rotulo(linha.DS_CONTA) not in rotulos
    ):
        raise _FalhaIndicador("conceito_nao_validado", nome)
    _validar_periodo(linha, ordem, observacao.DT_REFER, nome)

    fator = FATORES_ESCALA.get(linha.ESCALA_MOEDA)
    if (
        pd.isna(linha.MOEDA) or linha.MOEDA != "REAL" or fator is None
        or pd.isna(linha.FATOR_ESCALA_MOEDA) or linha.FATOR_ESCALA_MOEDA != fator
    ):
        raise _FalhaIndicador("moeda_escala_invalida", nome)
    if pd.isna(linha.VL_CONTA):
        raise _FalhaIndicador("valor_ausente", nome)
    try:
        valor = Decimal(linha.VL_CONTA)
    except InvalidOperation as erro:
        raise _FalhaIndicador("valor_invalido", nome) from erro
    if not valor.is_finite():
        raise _FalhaIndicador("valor_invalido", nome)
    if regra.saldo_nao_negativo and valor < 0:
        raise _FalhaIndicador("sinal_invalido", nome)

    fonte = {
        "CONCEITO": nome,
        "FAMILIA": linha.FAMILIA,
        "CD_CONTA": linha.CD_CONTA,
        "DS_CONTA": linha.DS_CONTA,
        "ORDEM_EXERC": ordem,
        "DT_INI_EXERC": _data_texto(linha.DT_INI_EXERC),
        "DT_FIM_EXERC": _data_texto(linha.DT_FIM_EXERC),
        "ID_DOC": linha.ID_DOC,
        "ARQUIVO_ORIGEM": linha.ARQUIVO_ORIGEM,
        "LINHA_ORIGEM": int(linha.LINHA_ORIGEM),
        "MOEDA": linha.MOEDA,
        "ESCALA_MOEDA": linha.ESCALA_MOEDA,
        "VL_CONTA": linha.VL_CONTA,
    }
    return _Insumo(valor * fator, linha.DT_INI_EXERC, linha.DT_FIM_EXERC, fonte)


def _validar_observacao(observacao, chave: tuple, tem_fatos: bool) -> None:
    if any(pd.isna(parte) for parte in chave):
        raise _FalhaIndicador("chave_incompleta", "A chave de entrega e escopo deve estar completa.")
    setor = observacao.GRUPO_SETORIAL
    if pd.isna(setor) or setor not in {"nao_financeira", "financeira", "regime_especifico"}:
        raise _FalhaIndicador("setor_nao_classificado", "A classificação setorial é insuficiente.")
    if setor != "nao_financeira":
        raise _FalhaIndicador("setor_nao_elegivel", setor)
    if not tem_fatos:
        raise _FalhaIndicador("sem_fatos", "A entrega na versão e escopo indicados está sem fatos.")


def calcular_indicadores(
    fatos_selecionados: pd.DataFrame,
    universo: pd.DataFrame,
    *,
    conflitos: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Calcula uma linha por observação e protótipo em uma captura.

    O universo define o denominador de cobertura, incluindo entregas sem fatos.
    Os fatos selecionados e as chaves em conflito vêm da auditoria de duplicatas.
    Cada linha mantém a chave do universo, a situação e as fontes dos insumos validados.
    """
    if universo.duplicated(list(CHAVE_PAINEL)).any():
        raise ValueError("Há observações repetidas no universo de indicadores.")
    if not universo["ESCOPO"].isin(("con", "ind")).all():
        raise ValueError("O escopo do universo deve ser con ou ind.")

    observacoes_com_fatos = fatos_selecionados[list(CHAVE_PAINEL)].drop_duplicates()
    presentes = set(observacoes_com_fatos.itertuples(index=False, name=None))
    indices = defaultdict(lambda: defaultdict(list))
    for linha in _contas_relevantes(fatos_selecionados).itertuples(index=False):
        indices[_chave_observacao(linha)][_chave_conta(linha)].append(linha)
    bloqueios = defaultdict(set)
    if conflitos is not None:
        presentes.update(conflitos[list(CHAVE_PAINEL)].itertuples(index=False, name=None))
        for linha in _contas_relevantes(conflitos).itertuples(index=False):
            bloqueios[_chave_observacao(linha)].add(_chave_conta(linha))

    resultados = []
    with localcontext() as contexto:
        contexto.prec = 38
        for observacao in universo.itertuples(index=False):
            chave = _chave_observacao(observacao)
            for indicador, prototipo in PROTOTIPOS.items():
                insumos = []
                valor = None
                situacao = "valido"
                detalhe = None
                try:
                    _validar_observacao(observacao, chave, chave in presentes)
                    for conceito, ordem in prototipo.insumos:
                        insumos.append(
                            _ler_insumo(indices[chave], bloqueios[chave], conceito, ordem, observacao)
                        )
                    if len({insumo.fonte["ID_DOC"] for insumo in insumos}) != 1:
                        raise _FalhaIndicador("vinculo_invalido", "Os insumos citam documentos distintos.")
                    valor = float(prototipo.formula(*insumos))
                except _FalhaIndicador as erro:
                    situacao, detalhe = erro.situacao, str(erro)
                resultados.append({
                    **dict(zip(universo.columns, observacao, strict=True)),
                    "INDICADOR": indicador,
                    "EIXO": prototipo.eixo,
                    "VALOR": valor,
                    "SITUACAO": situacao,
                    "DETALHE": detalhe,
                    "FONTES": json.dumps([insumo.fonte for insumo in insumos], ensure_ascii=False),
                })

    colunas = [*universo.columns, "INDICADOR", "EIXO", "VALOR", "SITUACAO", "DETALHE", "FONTES"]
    return pd.DataFrame(resultados, columns=colunas).astype({"VALOR": "Float64"})
