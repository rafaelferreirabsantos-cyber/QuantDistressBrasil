"""Configurações identificáveis da avaliação descritiva da Sprint 03B."""

import hashlib
import json
from dataclasses import asdict, dataclass

from quantdistress.evaluation.revision03 import MACROSETORES


VERSAO_METODOLOGICA = "03b.1"
MODO_TEMPORAL = "descritivo_revisado"
COMPONENTES = {
    "Q1": ("rentabilidade_operacional_ativos", 1),
    "Q2": ("fluxo_caixa_operacional_sobre_receita", 1),
    "D1": ("liquidez_corrente", -1),
    "D2": ("patrimonio_liquido_sobre_ativo", -1),
    "D3": ("financiamentos_reportados_sobre_ativo", 1),
}
PESOS = {
    "iguais": (1 / 2, 1 / 2, 1 / 3, 1 / 3, 1 / 3),
    "economicos": (0.6, 0.4, 0.4, 0.4, 0.2),
}


def hash_canonico(objeto) -> str:
    serializado = json.dumps(objeto, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Scenario:
    """Definição imutável de um cenário. Cada variante tem identificação própria."""

    name: str = "benchmark"
    min_peers: int = 30
    macro: bool = False
    method: str = "percentil"
    weights: str = "iguais"
    holdings: bool = True
    composition: str = "original"

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip() or type(self.min_peers) is not int or self.min_peers < 2:
            raise ValueError("Informe um nome e pelo menos dois pares por cenário.")
        if type(self.macro) is not bool or type(self.holdings) is not bool:
            raise ValueError("Macrosetores e holdings exigem parâmetros booleanos explícitos.")
        if self.method not in {"percentil", "robusto"} or self.weights not in PESOS:
            raise ValueError("Método de normalização ou esquema de pesos desconhecido.")
        if self.composition not in {"original", "retirada_20pct", "retirada_20pct_b"}:
            raise ValueError("Composição de referência desconhecida.")

    @property
    def component_weights(self) -> dict[str, float]:
        return dict(zip(COMPONENTES, PESOS[self.weights], strict=True))

    @property
    def config_id(self) -> str:
        return hash_canonico(self.metadata())

    def metadata(self) -> dict:
        pesos = self.component_weights
        return {
            **asdict(self), "versao_metodologica": VERSAO_METODOLOGICA, "modo_temporal": MODO_TEMPORAL,
            "referencia": "setor_fca_ano_escopo_sem_alvo", "minimo_valores_distintos": 2,
            "macrosetores": "sprint03a_candidatos_v1" if self.macro else None,
            "mapeamento_macrosetores": {macro: list(setores) for macro, setores in MACROSETORES.items()} if self.macro else {},
            "escopo_individual": "apenas_sem_consolidado_confirmado_na_fonte_e_sem_holding",
            "componentes": {
                nome: {"indicador": indicador, "direcao": direcao, "peso": pesos[nome]}
                for nome, (indicador, direcao) in COMPONENTES.items()
            },
        }
