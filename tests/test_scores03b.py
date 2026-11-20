import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from quantdistress.features.indicators import PROTOTIPOS
from quantdistress.scoring.experimental import (
    COMPONENTES,
    METADADOS,
    METADADOS_FONTE,
    MODO_TEMPORAL,
    PRESSAO,
    Scenario,
    calculate_scores,
    load_panel,
)


def _emitente(cvm, valores=(1, 1, 1, 1, 1), *, escopo="con", ano=2024, setor="Energia Elétrica",
              data=None, consolidado=True, bloqueios=None, caixa=None, cnpj=None, doc=None):
    bloqueios = bloqueios or {}
    entrada = dict.fromkeys([*METADADOS, *METADADOS_FONTE])
    entrada.update(
        CD_CVM=str(cvm), CNPJ_CIA=cnpj or str(cvm).zfill(14), ANO_ARQUIVO=ano,
        DT_REFER=pd.Timestamp(data or f"{ano}-12-31"), ESCOPO=escopo, ID_DOC=doc or f"doc{cvm}-{data}", VERSAO=1,
        SETOR_FCA=setor, GRUPO_SETORIAL="nao_financeira", VINCULO_FCA="unico", SITUACAO_ENTREGA_DFP="unica",
        MODO_TEMPORAL=MODO_TEMPORAL, CONSOLIDADO_NA_FONTE=consolidado, SHA256_DFP="x" * 64,
        LINK_DOC="https://dados.cvm.gov.br/exemplo", DT_DIVULGACAO=pd.Timestamp(f"{ano + 1}-03-15"),
    )
    itens = [(nome, indicador, valor, bloqueios.get(nome, "valido"))
             for (nome, (indicador, _)), valor in zip(COMPONENTES.items(), valores, strict=True)]
    if caixa is not None:
        itens.append(("PRESSAO", PRESSAO, np.nan, "denominador_invalido"))
    for nome, indicador, valor, status in itens:
        fontes = [{"CONCEITO": conceito, "ID_DOC": entrada["ID_DOC"], "ARQUIVO_ORIGEM": "membro.csv", "LINHA_ORIGEM": pos + 1}
                  for pos, (conceito, _) in enumerate(PROTOTIPOS[indicador].insumos)]
        if nome == "PRESSAO":
            fontes[0]["VL_CONTA"], fontes[1]["VL_CONTA"] = str(caixa), "0.0"
        if status == "linhagem_falsa":
            status = "valido"
            fontes[0]["ID_DOC"] = "outro"
        yield dict(entrada, INDICADOR=indicador, VALOR=valor, SITUACAO=status,
                   DETALHE=None, FONTES=json.dumps(fontes, ensure_ascii=False))


def _painel(*emitentes):
    return pd.DataFrame([linha for emitente in emitentes for linha in emitente])


def _alvo(componentes, cvm="1", escopo="con", ano=2024):
    return componentes.query("CD_CVM == @cvm and ESCOPO == @escopo and ANO_ARQUIVO == @ano").set_index("COMPONENTE")


def test_percentis_monotonicos_empates_e_inversoes_economicas():
    painel = _painel(
        _emitente(1, (0, 0, 1, -1, 3), caixa=12), _emitente(2, (0, 1, 2, 0, 2)),
        _emitente(3, (2, 2, 3, 1, 1)), _emitente(4, (3, 3, 4, 2, 0)),
    )
    wide, componentes = calculate_scores(painel, Scenario(min_peers=2))
    alvo = _alvo(componentes)
    assert alvo["N_PARES"].tolist() == [3] * 5
    assert alvo["PONTOS"].tolist() == pytest.approx([100 / 6, 0, 100, 100, 100])
    wide = wide.set_index("CD_CVM")
    assert wide.loc["1", "QUALITY_SCORE"] == pytest.approx(100 / 12)
    assert wide.loc["1", "FINANCIAL_DISTRESS_SCORE"] == pytest.approx(100.0)
    assert wide["FINANCIAL_DISTRESS_SCORE"].is_monotonic_decreasing
    assert wide["QUALITY_SCORE"].is_monotonic_increasing
    assert wide.loc["1", "LIQUIDEZ_CORRENTE"] == 1
    assert wide.loc["1", "PATRIMONIO_LIQUIDO_NEGATIVO"]
    assert wide.loc["1", "MARCADOR_CAIXA"] == "caixa_zero_com_financiamento"


def test_pesos_e_secao_independente_com_denominador_ou_componente_indisponivel():
    painel = _painel(_emitente(1, (0, np.nan, 1, 1, 1), bloqueios={"Q2": "denominador_invalido"}, caixa=0),
                     _emitente(2, (1, 1, 2, 2, 2)), _emitente(3, (2, 2, 3, 3, 3)), _emitente(4, (3, 3, 4, 4, 4)))
    iguais, c = calculate_scores(painel, Scenario(min_peers=2))
    economicos, _ = calculate_scores(painel, Scenario("sensibilidade", min_peers=2, weights="economicos"))
    a, e = iguais.set_index("CD_CVM").loc["1"], economicos.set_index("CD_CVM").loc["1"]
    assert pd.isna(a.QUALITY_SCORE) and pd.isna(e.QUALITY_SCORE)
    assert a.DISPONIBILIDADE_QUALITY == 0.5
    assert e.DISPONIBILIDADE_QUALITY == 0.6
    assert a.FINANCIAL_DISTRESS_SCORE == pytest.approx(200 / 3)
    assert e.FINANCIAL_DISTRESS_SCORE == pytest.approx(80)
    assert _alvo(c).loc["Q2", "SITUACAO"] == "denominador_invalido"
    assert a.MARCADOR_CAIXA == "caixa_zero_sem_financiamento_reportado"


def test_componente_obrigatorio_ausente_preserva_a_outra_dimensao():
    painel = _painel(*(_emitente(i, (i, i, i, i, i)) for i in range(1, 5)))
    q2 = COMPONENTES["Q2"][0]
    sem_componente = painel.loc[~(painel.CD_CVM.eq("1") & painel.INDICADOR.eq(q2))]
    wide, cmp = calculate_scores(sem_componente, Scenario(min_peers=2))
    assert wide.loc[0, "STATUS_QUALITY"] == "bloqueado"
    assert wide.loc[0, "STATUS_DISTRESS"] == "calculado"
    assert _alvo(cmp).loc["Q2", "SITUACAO"] == "indicador_ausente"
    assert _alvo(cmp).loc["Q2", "S_ESTATISTICO"] == "utilizavel"


def test_escopos_anos_setores_dimensoes_e_ausencia_de_consolidado_sao_independentes():
    painel = _painel(
        _emitente(1), _emitente(2, (2, 2, 2, 2, 2)),
        _emitente(3, (3, 3, 3, 3, 3), escopo="ind", consolidado=False),
        _emitente(4, escopo="ind", consolidado=None), _emitente(5, escopo="ind", consolidado=True),
        _emitente(6, setor="Comércio (Atacado e Varejo)"), _emitente(1, ano=2023),
        _emitente(7, setor="Emp. Adm. Part. - Energia Elétrica", escopo="ind", consolidado=False),
    )
    wide, cmp = calculate_scores(painel, Scenario(min_peers=2))
    assert wide.QUALITY_SCORE.isna().all()
    assert _alvo(cmp)["N_PARES"].tolist() == [1] * 5
    assert _alvo(cmp, cvm="3", escopo="ind")["N_PARES"].tolist() == [0] * 5
    assert _alvo(cmp, ano=2023)["N_PARES"].tolist() == [0] * 5
    decisao = wide.set_index("CD_CVM").ELEGIBILIDADE_UNIVERSO
    assert decisao.loc["4"] == "consolidado_sem_evidencia"
    assert decisao.loc["5"] == "consolidado_presente_na_fonte"
    assert decisao.loc["7"] == "holding_individual"
    assert _alvo(cmp, cvm="6")["S_ESTATISTICO"].eq("insuficiente").all()


def test_macro_preserva_exato_e_ultimo_documento_e_independente_da_qualidade():
    painel = _painel(
        _emitente(1, setor="Saneamento, Serv. Água e Gás"), _emitente(2),
        _emitente(3, (2, 2, 2, 2, 2)), _emitente(4, (3, 3, 3, 3, 3)),
        _emitente(5, data="2024-01-01"), _emitente(5, bloqueios={"Q1": "periodo_incompativel"}),
        _emitente(6, cnpj="00000000000006", doc="seis-a"), _emitente(6, cnpj="00000000000606", doc="seis-b"),
        _emitente(7, setor="Emp. Adm. Part. - Energia Elétrica"),
    )
    wide, cmp = calculate_scores(painel, Scenario("macro", min_peers=2, macro=True))
    assert _alvo(cmp).REFERENCIA_TIPO.eq("macrosetor_candidato").all()
    assert _alvo(cmp, cvm="2").REFERENCIA_TIPO.eq("setor_exato").all()
    assert _alvo(cmp, cvm="7").REFERENCIA_TIPO.eq("setor_exato").all()
    w = wide.set_index("CD_CVM")
    assert w.loc["1", "REF_GRUPO_Q1"] == "utilidades"
    assert w.loc["1", "N_PARES_Q1"] >= 2
    assert w.loc["1", "COMPOSICAO_REFERENCIA_QUALITY"] == "macrosetor_candidato"
    assert pd.isna(w.loc["5", "QUALITY_SCORE"]) and w.loc["5", "DT_REFER"] == pd.Timestamp("2024-12-31")
    assert w.loc["6", "ELEGIBILIDADE_UNIVERSO"] == "documento_ambiguo"
    assert w.loc["6", "N_DOCUMENTOS_CANDIDATOS"] == 2
    assert len(json.loads(w.loc["6", "DOCUMENTOS_CANDIDATOS"])) == 2
    assert pd.isna(w.loc["6", "QUALITY_SCORE"]) and pd.isna(w.loc["6", "CNPJ_CIA"])


def test_constantes_linhagem_e_classificacao_temporal():
    painel = _painel(_emitente(1, bloqueios={"Q1": "linhagem_falsa"}), _emitente(2), _emitente(3), _emitente(4))
    wide, cmp = calculate_scores(painel, Scenario(min_peers=2))
    a = _alvo(cmp)
    assert a.A_CONTABIL.loc["Q1"] == "linhagem_incompleta"
    assert a.DISPONIVEL.loc["Q1"]
    assert a.S_ESTATISTICO.eq("constante").all()
    assert wide.QUALITY_SCORE.isna().all()
    assert wide.ELEGIBILIDADE_TEMPORAL.eq("bloqueada_sem_evidencia").all()
    assert wide.DT_DIVULGACAO.notna().all()
    assert a.CODIGOS_PARES_SHA256.map(len).eq(64).all()
    with pytest.raises(ValueError, match="descritivo revisado"):
        calculate_scores(painel.assign(MODO_TEMPORAL="historico"), Scenario(min_peers=2))
    with pytest.raises(ValueError, match="exercício contábil"):
        calculate_scores(painel.assign(ANO_ARQUIVO=2023), Scenario(min_peers=2))


def test_reproducibilidade_com_base_permutada_e_composicao_controlada():
    painel = _painel(*(_emitente(i, (i, i, i, i, i)) for i in range(1, 8)))
    scenario = Scenario("retirada", min_peers=2, composition="retirada_20pct")
    wide, cmp = calculate_scores(painel, scenario)
    embaralhado = painel.sample(frac=1, random_state=8)
    wide_ord, cmp_ord = calculate_scores(embaralhado, scenario)
    assert_frame_equal(wide, wide_ord)
    assert_frame_equal(cmp, cmp_ord)
    assert cmp.N_PARES.eq(5).all()
    assert cmp.ID_REFERENCIA.notna().all()
    assert scenario.config_id != Scenario("retirada", min_peers=2).config_id


def test_carregamento_valida_modo_hash_e_particao_e_bloqueia_ind_com_fonte_ausente(tmp_path: Path):
    painel = _painel(_emitente(9, escopo="ind", consolidado=False))
    ano = tmp_path / "2024"
    ano.mkdir()
    painel.to_parquet(ano / "indicadores.parquet", index=False)
    manifesto = {"modo_temporal": MODO_TEMPORAL, "anos": [
        {"ano": 2024, "fonte_dfp": {"sha256": "x" * 64, "url_oficial": "https://dados.cvm.gov.br/dfp"},
         "sha256_fca": "y" * 64, "url_fca": "https://dados.cvm.gov.br/fca", "observacoes_indicadores": len(painel)}
    ]}
    path = tmp_path / "manifesto.json"
    path.write_text(json.dumps(manifesto), encoding="utf-8")
    carregado = load_panel(tmp_path, tmp_path / "sem-dados")
    assert carregado.CONSOLIDADO_NA_FONTE.isna().all()
    w, _ = calculate_scores(carregado, Scenario(min_peers=2))
    assert w.loc[0, "ELEGIBILIDADE_UNIVERSO"] == "consolidado_sem_evidencia"
    assert w.loc[0, "URL_OFICIAL_FCA"] == "https://dados.cvm.gov.br/fca"
    manifesto["anos"][0]["fonte_dfp"]["sha256"] = "z" * 64
    path.write_text(json.dumps(manifesto), encoding="utf-8")
    with pytest.raises(ValueError, match="Partição incompatível"):
        load_panel(tmp_path, tmp_path / "sem-dados")
