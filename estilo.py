import numpy as np

# formatos utilizados na tabela
f = [
    {'locale': {'decimal': ',', 'group': '.'}, 'nully': '', 'prefix': 1000000, 'specifier': ',.0'},
    {'locale': {'decimal': ',', 'group': '.'}, 'nully': '', 'prefix': None, 'specifier': ',.1%'}
]

# colunas que seram exibidas na tabela, para cada setor
# o nome das colunas devem ser o mesmo dos nomes definidos no arquivo funcoes.py
# o 1o item da lista indica qual o formato usar, conforme ordem em f (0 - milhar, 1 - porcentagem)
# o 2o item indica qual grafico será plotado (numero de 0 a 2)
geral = {
    'Pat. Líq.': [0, 0],
    'Receita Líq.': [0, 0],
    'M. Bruta': [1, 1],
    'EBIT': [0, 0],
    'EBITIDA': [0, 0],
    'Res. Fin.': [0, 0],
    'Lucro Líq.': [0, 0],
    'M. Líq.': [1, 1],
    'ROE': [1, 1],
    'D&A': [0, 2],
    'Op. Desc.': [0, 2],
    'Imposto': [0, 2],
    'Dívida': [0, 2],
    'D.L./EBITIDA': [1, 1],
    'Caixa': [0, 2],
    'FCO': [0, 2],
    'CAPEX': [0, 2],
    'FCF': [0, 2],
    'Prov.': [0, 2],
    'Payout': [1, 1]
}

seguro = {
    'Pat. Líq.': [0, 0],
    'Receita Líq.': [0, 0],
    'EBIT': [0, 0],
    'Res. Fin.': [0, 0],
    'Lucro Líq.': [0, 0],
    'M. Líq.': [1, 1],
    'ROE': [1, 1],
    'Caixa': [0, 2],
    'FCO': [0, 2],
    'FCF': [0, 2],
    'Prov.': [0, 2],
    'Payout': [1, 1]
}

banco = {
    'Pat. Líq.': [0, 0],
    'Receita Inter. Fin.': [0, 0],
    'Lucro Líq.': [0, 0],
    'M. Líq.': [1, 1],
    'ROE': [1, 1],
    'Índ. Basileia': [1, 1],
    'Índ. Imobilização': [1, 1],
    'PDD': [0, 2],
    'PDD/Lucro Líq.': [1, 1],
    'Prov.': [0, 2],
    'Payout': [1, 1]
}

# deve seguir a mesma ordem da lista funcoes_valores no arquivo funcoes.py
conjunto = [geral, banco, seguro]

# NOTA: as cores no arquivo estilo.css tambem devem ser mudadas
cor = {
    'fundo': '#1C1C1C',
    'fonte': '#EEEEEE',
    'busca': '#333333',
    'grid': '#424242',
    'graf': '#282828',
    'amarelo': '#FF991F',
    'vermelho': '#DE350B',
    'azul': '#00A3BF',
    'verde':'#006644',
    'verde_texto': '#00897B',
    'amarelo_texto': '#FFA000',
    'vermelho_texto': '#C62828'
}


# estilo dos cabecalhos
estilo_cabecalho = [
    {
        'if': {'column_id': 'DT_MA'},
        'backgroundColor': cor['graf']
    },
    {
        'if': {'column_id': ['D&A','Op. Desc.','Imposto','Dívida','D.L./EBITIDA']},
        'backgroundColor': cor['vermelho']
    },
    {
        'if': {'column_id': ['Caixa','FCO','CAPEX','FCF',]},
        'backgroundColor': cor['azul']
    },
    {
        'if': {'column_id': ['Prov.','Payout']},
        'backgroundColor': cor['amarelo']
    }
]

# estilo das colunas (cor da fonte)

# campos com regras especies
campos = ['D.L./EBITIDA','Índ. Basileia','Índ. Imobilização','PDD/Lucro Líq.']
lim_verde = [1.0, 0.1, 0.4, 0.8] # se menor que valor, verde
lim_ver = [3.0, 0.15, 0.5, 1.0] # se maior que valor, vermelho

estilo_dados = [
    {
        'if': {'column_id': 'DT_MA'}, # coluna data
        'backgroundColor': cor['graf']
    },
    {
        'if': {'filter_query': '{Payout} > 0.5', 'column_id': 'Payout'}, # se maior que 50%, verde
        'color': cor['verde_texto']
    },
    {
        'if': {'column_id': ['Dívida','PDD']}, # sempre vermelho
        'color': cor['vermelho_texto']
    },
] + [
    { # se maior que zero, verde
        'if': {'filter_query': '{{{}}} > 0'.format(c), 'column_id': c},
        'color': cor['verde_texto']
    } for c in ['EBIT','EBITIDA','Res. Fin.','Lucro Líq.','Receita Inter. Fin.']
] + [
    { # se menor que zero, vermelho
        'if': {'filter_query': '{{{}}} < 0'.format(c), 'column_id': c},
        'color': cor['vermelho_texto']
    } for c in ['Pat. Líq.','EBIT','EBITIDA','Res. Fin.','Receita Inter. Fin.','Lucro Líq.','M. Líq.','ROE','FCO']
] + [
    { # se menor que valor, verde
        'if': {'filter_query': '{{{}}} < {}'.format(c,v), 'column_id': c},
        'color': cor['verde_texto']
    } for (c,v) in zip(campos, lim_verde)
] + [
    { # se entre valor, amarelo
        'if': {'filter_query': '{{{}}} > {} && {{{}}} < {}'.format(c,v,c,v2), 'column_id': c},
        'color': cor['amarelo_texto']
    } for (c,v,v2) in zip(campos, lim_verde, lim_ver)
] + [
    { # se maior que valor, vermelho
        'if': {'filter_query': '{{{}}} > {}'.format(c,v2), 'column_id': c},
        'color': cor['vermelho_texto']
    } for (c,v2) in zip(campos, lim_ver)
]


###########################################
# não mudar
colunas = [list(item.keys()) for item in conjunto]
tmp = [list(item.values()) for item in conjunto]

formatos = [[f[item2[0]] for item2 in item] for item in tmp]
col1 = [{'name': 'Data', 'id': 'DT_MA', 'type': 'text'}]
cols_table = [col1+[{'name': x, 'id': x, 'type': 'numeric', 'format': y} for (x,y) in zip(col, fo)] \
    for (col,fo) in zip(colunas, formatos)]

colunas = [np.array(item) for item in colunas]
graficos = [np.array([item2[1] for item2 in item]) for item in tmp]
cols_graf = [[col[gr == 0]] + [col[gr == 1]] + [col[gr == 2]] for (col, gr) in zip(colunas, graficos)]
