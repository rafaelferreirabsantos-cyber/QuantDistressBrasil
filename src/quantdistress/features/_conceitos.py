"""Conceitos monetários de contas fixas para o leiaute não financeiro da DFP."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Conceito:
    familias: tuple[str, ...]
    codigo: str
    rotulos: tuple[str, ...]
    rotulo_individual: str | None = None
    saldo_nao_negativo: bool = False

    def rotulos_do_escopo(self, escopo: str) -> tuple[str, ...]:
        if escopo == "ind" and self.rotulo_individual is not None:
            return (self.rotulo_individual,)
        return self.rotulos


CONCEITOS = {
    "ativo_total": Conceito(("BPA",), "1", ("Ativo Total",), saldo_nao_negativo=True),
    "ativo_circulante": Conceito(
        ("BPA",), "1.01", ("Ativo Circulante",), saldo_nao_negativo=True,
    ),
    "caixa_equivalentes": Conceito(
        ("BPA",), "1.01.01", ("Caixa e Equivalentes de Caixa",), saldo_nao_negativo=True,
    ),
    "passivo_circulante": Conceito(
        ("BPP",), "2.01", ("Passivo Circulante",), saldo_nao_negativo=True,
    ),
    "financiamentos_circulantes": Conceito(
        ("BPP",), "2.01.04", ("Empréstimos e Financiamentos",), saldo_nao_negativo=True,
    ),
    "financiamentos_nao_circulantes": Conceito(
        ("BPP",), "2.02.01", ("Empréstimos e Financiamentos",), saldo_nao_negativo=True,
    ),
    "patrimonio_liquido": Conceito(
        ("BPP",), "2.03", ("Patrimônio Líquido Consolidado",),
        rotulo_individual="Patrimônio Líquido",
    ),
    "receita_vendas_servicos": Conceito(
        ("DRE",), "3.01", ("Receita de Venda de Bens e/ou Serviços",),
    ),
    "resultado_antes_financeiro_tributos": Conceito(
        ("DRE",), "3.05", ("Resultado Antes do Resultado Financeiro e dos Tributos",),
    ),
    "fluxo_caixa_operacional": Conceito(
        ("DFC_MD", "DFC_MI"), "6.01",
        ("Caixa Líquido Atividades Operacionais", "Caixa Líquido das Atividades Operacionais"),
    ),
}
