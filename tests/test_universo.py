from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from quantdistress.data.universe import construir_universo, ler_cadastro_atual, ler_fca


def _fontes(tmp_path: Path):
    cabecalho = (
        'CNPJ_Companhia;Codigo_CVM;Data_Referencia;Versao;ID_Documento;'
        'Setor_Atividade;Situacao_Registro_CVM;Situacao_Emissor\n'
    )
    with ZipFile(tmp_path / 'fca.zip', 'w') as pacote:
        geral = (
            cabecalho
            + '00000000000001;1;2024-01-01;1;a;Alimentos;Ativo;Fase Operacional\n'
            + '00000000000001;1;2024-01-01;2;b;Emp. Adm. Part. - Energia Elétrica;Ativo;Fase Operacional\n'
            + '00000000000002;2;2024-01-01;1;c;Bancos;Ativo;Fase Operacional\n'
            + '00000000000002;2;2024-01-01;1;d;Alimentos;Ativo;Fase Operacional\n'
            + '00000000000003;3;2025-01-01;1;e;Bancos;Ativo;Fase Operacional\n'
        )
        pacote.writestr('fca_cia_aberta_geral_2024.csv', geral.encode('latin-1'))
        indice = (
            'CNPJ_CIA;CD_CVM;DT_REFER;VERSAO;ID_DOC;DT_RECEB\n'
            '00.000.000/0000-01;000001;2024-01-01;2;b;2025-04-01\n'
            '00.000.000/0000-02;000002;2024-01-01;1;c;2024-05-01\n'
        )
        pacote.writestr('fca_cia_aberta_2024.csv', indice.encode('latin-1'))
    (tmp_path / 'cad.csv').write_text(
        'CNPJ_CIA;CD_CVM;SIT;DT_CANCEL\n'
        '00000000000001;1;CANCELADA;2025-04-01\n'
        '00000000000001;1;CANCELADA;2025-04-01\n'
        '00000000000002;2;CANCELADA;2025-04-01\n'
        '00000000000002;2;ATIVO;\n', encoding='latin-1',
    )
    return ler_fca(tmp_path / 'fca.zip', 2024), ler_cadastro_atual(tmp_path / 'cad.csv')


def test_universo_usa_fca_do_periodo_e_retem_emissor_cancelado(tmp_path):
    fca, cadastro = _fontes(tmp_path)
    entregas = pd.DataFrame({
        'CNPJ_CIA': ['00.000.000/0000-01'] * 2 + ['00.000.000/0000-02'] * 2 + ['00.000.000/0000-03'],
        'CD_CVM': ['000001', '000001', '000002', '000002', '000003'],
        'DT_REFER': [pd.Timestamp('2024-12-31')] * 5,
        'VERSAO': [1, 2, 1, 1, 1],
        'DT_RECEB': [pd.Timestamp('2025-05-01')] * 5,
        'ID_DOC': list('ABCDE'),
        'LINK_DOC': ['https://example.invalid'] * 5,
    })
    universo = construir_universo(entregas, fca, cadastro)
    assert len(universo) == 6
    assert set(universo['ESCOPO']) == {'con', 'ind'}
    con = universo.loc[universo.ESCOPO.eq('con')].set_index('CD_CVM')
    primeira = con.loc['000001']
    assert primeira['ID_DOC'] == 'B' and primeira['VERSAO'] == 2
    assert primeira['GRUPO_SETORIAL'] == 'nao_financeira'
    assert primeira['FCA_RECEBIDA_APOS_REFERENCIA']
    assert primeira['CANCELAMENTO_POSTERIOR']
    assert con.loc['000002', 'SITUACAO_ENTREGA_DFP'] == 'ambigua'
    assert pd.isna(con.loc['000002', 'ID_DOC'])
    assert con.loc['000002', 'VINCULO_FCA'] == 'ambiguo'
    assert con.loc['000002', 'VINCULO_CAD_COLETA'] == 'ambiguo'
    assert con.loc['000003', 'GRUPO_SETORIAL'] == 'nao_classificada'
    assert con['DT_DIVULGACAO'].isna().all()
