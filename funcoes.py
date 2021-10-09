from os.path import exists
import requests
import operator
from zipfile import ZipFile
import numpy as np
import pandas as pd
from unidecode import unidecode
import nltk

########################################
# ALTERAR AQUI PARA MODIFICAR FUNDAMENTOS OBTIDOS NOS ARQUIVOS

# GERAL - aplicado a todos os setores menos os em filtro_setor
fund_geral = {'CD_CONTA': ['1.01.01', '1.01.02', \
                           '2.03', '2.01.04', '2.02.01', \
                           '3.01', '3.02', '3.05', '3.06', '3.08', '3.09', '3.10', \
                           '6.01', '6.03', \
                           'CAPEX', 'proventos', 'dea'], \
            'nome_conta': ['Caixa', 'Caixa', \
                           'Pat. Líq.', 'Dívida', 'Dívida', \
                           'Receita Líq.', 'CPV', 'EBIT', 'Res. Fin.', 'Imposto', 'Lucro Líq.', 'Op. Desc.', \
                           'FCO', 'FCF', \
                           'CAPEX', 'Prov.', 'D&A']}
fund_geral = pd.DataFrame(fund_geral)

def valores_geral(df_geral):
    # print("Geral")
    df = df_geral.merge(fund_geral, on='CD_CONTA')
    
    df = pd.pivot_table(df, index=['demo1','CD_CVM','DT_FIM_EXERC'], \
        columns='nome_conta', values='VL_CONTA', aggfunc=np.nansum).reset_index()
    
    df['EBITIDA'] = df['EBIT'] + df['D&A']
    df['M. Bruta'] = (df['Receita Líq.'] + df['CPV']) / df['Receita Líq.']
    df['M. Líq.'] = df['Lucro Líq.'] / df['Receita Líq.']
    df['ROE'] = df['Lucro Líq.'] / df['Pat. Líq.']
    df['D.L./EBITIDA'] = (df['Dívida'] - df['Caixa']) / df['EBITIDA']
    df['FCL CAPEX'] = df['FCO'] + df['CAPEX']
    df['Prov.'] = df['Prov.'] * -1
    df['Payout'] = df['Prov.'] / df['Lucro Líq.']

    return df

   
#  BANCOS
fund_banco = {'NomeColuna': [78186, 78187, 79664, \
                             79662, 78208, 78213], \
            'nome_conta': ['Pat. Líq.','Lucro Líq.','Índ. Basileia', \
                           'Índ. Imobilização','Receita Inter. Fin.','PDD']}
fund_banco = pd.DataFrame(fund_banco)

def valores_banco(df_banco):
    # print("Bancos")
    # ler e ajustar IFDATA
    df = pd.read_csv("dados/IFDATA.zip", sep=';', encoding="mbcs")
    df['demo1'] = "ITR"
    df['demo2'] = "Resumo"
    df.loc[df.nome_conta.isin(['Receita Inter. Fin.','PDD', 'Lucro Líq.']),'demo2'] = "DRE"
    df['data'] = pd.to_datetime(df.data, format="%Y%m") + pd.offsets.MonthEnd(0)
    df.rename(columns={'data':'DT_FIM_EXERC', 'Codigo_CVM':'CD_CVM', 'v':'VL_CONTA'}, inplace=True)
    
    # Copiar dados das ITRs para a DFP
    # Resumo e DFP
    df['mes'] = df['DT_FIM_EXERC'].dt.month
    index_dre = df.demo2 == "DRE"
    df2 = df.loc[~index_dre & (df.mes == 12)].copy()
    df2['demo1'] = "DFP"

    # DRE e ITR
    df3 = df.loc[index_dre].copy()
    df3['ano'] = df3['DT_FIM_EXERC'].dt.year
    df4 = df3[df3.mes.isin([3, 9])].copy()
    df4.mes += 3
    df3 = df3.merge(df4, on=['CD_CVM','nome_conta','ano','mes'], how="left", suffixes=['','_i']).reset_index()
    df3.loc[df3['VL_CONTA_i'].isna(), 'VL_CONTA_i'] = 0
    df3['VL_CONTA'] = df3['VL_CONTA'] - df3['VL_CONTA_i']

    # DRE e DFP
    df4 = df3.groupby(['demo1','CD_CVM','nome_conta','ano'])
    df4 = df4.agg({'DT_FIM_EXERC': 'max', 'VL_CONTA': 'sum', 'index': 'count'}).reset_index()
    df4 = df4.loc[df4['index'] == 4]
    df4['demo1'] = "DFP"

    # Resumo e ITR
    df5 = df.loc[~index_dre]

    # obter os proventos
    df_prov = df_banco.loc[df_banco['CD_CONTA'] == "proventos"].copy()
    df_prov = df_prov.loc[df_prov['CD_CVM'].isin(df['CD_CVM'].unique())]
    df_prov['CD_CONTA'] = "Prov."
    df_prov.rename(columns={'CD_CONTA':'nome_conta'}, inplace=True)
    
    # concaternar e mudar de long para wide
    df = pd.concat([df2, df3, df4, df5, df_prov], join='inner')
    df = pd.pivot_table(df, index=['demo1','CD_CVM','DT_FIM_EXERC'], \
        columns='nome_conta', values='VL_CONTA', aggfunc=np.nansum).reset_index()
    
   
    df['M. Líq.'] = df['Lucro Líq.'] / df['Receita Inter. Fin.']
    df['ROE'] = df['Lucro Líq.'] / df['Pat. Líq.']
    df['PDD/Lucro Líq.'] = df['PDD'] / df['Lucro Líq.']
    df['Prov.'] = df['Prov.'] * -1
    df['Payout'] = df['Prov.'] / df['Lucro Líq.']

    return df



# SEGUROS
fund_seguro = {'CD_CONTA': ['1.01.01', '1.01.02', \
                            '2.03', 'proventos', \
                            '3.01', '3.07', '3.08', '3.10', '3.13', \
                            '6.01', '6.03'], \
            'nome_conta': ['Caixa', 'Caixa', \
                           'Pat. Líq.', 'Prov.', \
                           'Receita Líq.', 'EBIT', 'Res. Fin.', 'Imposto', 'Lucro Líq.', \
                           'FCO', 'FCF']}
fund_seguro = pd.DataFrame(fund_seguro)

def valores_seguro(df_seguro):
    # print("Seguros")
    df = df_seguro.merge(fund_seguro, on='CD_CONTA')
    
    df = pd.pivot_table(df, index=['demo1','CD_CVM','DT_FIM_EXERC'], \
        columns='nome_conta', values='VL_CONTA', aggfunc=np.nansum).reset_index()
    
    df['M. Líq.'] = df['Lucro Líq.'] / df['Receita Líq.']
    df['ROE'] = df['Lucro Líq.'] / df['Pat. Líq.']
    df['Prov.'] = df['Prov.'] * -1
    df['Payout'] = df['Prov.'] / df['Lucro Líq.']

    return df


filtro_setor = ["Bancos","Seguradoras e Corretoras"] # bancos deve ser o primeiro. Valores devem ser iguais à dados_companhia.csv, coluna Setor_Atividade
nome_arquivos = ["geral","bancos","seguros"]
funcoes_valores = [valores_geral, valores_banco, valores_seguro]
########################################

# funcões para obter outros fundamentos

stopwords = nltk.corpus.stopwords.words('portuguese')
stemmer = nltk.stem.RSLPStemmer()
# nltk.download('stopwords')
# nltk.download('RSLPStemmer')
def capex(dados):
    # considerado capex os lançamentos que começam com 6.02. e possuem pelo menos uma palavra do capex1 e
    # uma palavra do capex2, ou possuem uma palavra do capex2 sozinha
    capex1 = ['aquis', 'compr', 'adiç', 'aplic', 'desenvolv', 'invest', 'gast']
    capex2 = ['imobil', 'intangi', 'softw', 'biolog', 'permanent', 'terren', 'can', 'miner']
    index = dados.CD_CONTA.str.startswith("6.02.") & (dados.setor == 0) # calcular apenas para geral

    original = dados.DS_CONTA.loc[index]
    unicos = pd.Series(original.unique())

    tmp2 = unicos.str.lower()
    tmp2 = tmp2.str.replace("\.|,|/|;|\(|\)|-|ativo.", ' ', regex = True)
    tmp2 = tmp2.str.replace('í', 'i', regex = False)
    tmp2 = tmp2.str.replace('ó', 'o', regex = False)
    tmp2 = tmp2.apply(lambda x: ' '.join([stemmer.stem(word) for word in x.split() if word not in (stopwords)]))

    tmp3 = tmp2.apply(lambda x: len([word for word in x.split() if word in capex1]))
    tmp4 = tmp2.apply(lambda x: len([word for word in x.split() if word in capex2]))
    tmp5 = tmp2.apply(lambda x: True if x in capex2 else False)

    tmp = ((tmp3 > 0) & (tmp4 > 0)) | tmp5
  
    return filtrar(dados, index, tmp, unicos, "CAPEX", operator.gt)


def proventos(dados):
    index = dados.CD_CONTA.str.startswith("6.03.")

    original = dados.DS_CONTA.loc[index]
    unicos = pd.Series(original.unique())

    tmp2 = unicos.str.lower()
    tmp2 = tmp2.str.replace("\.|,|/|;|\(|\)|-|^IRRF| s | sobre ", ' ', regex = True)
    tmp2 = tmp2.apply(lambda x: unidecode(' '.join([stemmer.stem(word) for word in x.split() if word not in (stopwords)])))
    tmp2 = tmp2.str.replace("juros capital proprio|juros capital|capital proprio", 'jcp', regex = True)

    tmp3 = tmp2.apply(lambda x: len([word for word in x.split() if word in ['pag','distribuica','pgt']]))
    tmp4 = tmp2.apply(lambda x: len([word for word in x.split() if word in ['divid', 'capit', 'jscp', 'jcp']]))
    tmp5 = tmp2.apply(lambda x: True if x in ['divid', 'capit', 'jscp', 'jcp'] else False)

    tmp = ((tmp3 > 0) & (tmp4 > 0)) | tmp5

    return filtrar(dados, index, tmp, unicos, "proventos", operator.gt)
 

def dea(dados):
    index = dados.CD_CONTA.str.startswith("6.01.01.") & (dados.setor == 0) # calcular apenas para geral

    original = dados.DS_CONTA.loc[index]
    unicos = pd.Series(original.unique())

    tmp2 = unicos.str.lower()
    tmp2 = tmp2.str.replace("\.|,|/|;|\(|\)|-", ' ', regex = True)
    tmp2 = tmp2.apply(lambda x: ' '.join([stemmer.stem(word) for word in x.split() if word not in (stopwords)]))

    tmp3 = tmp2.apply(lambda x: len([word for word in x.split() if word in ['depreci','amort','exaust']]))

    return filtrar(dados, index, tmp3 > 0, unicos, "dea", operator.gt)


funcoes_fundamentos = [capex, proventos, dea]
"""
# para verificar funções acima

df = dados2.get_group(2)
x=df.loc[df.CD_CONTA.isin(['6.05.02'])]
x.DS_CONTA.value_counts()

x=df[df.DS_CONTA == "Depreciação e amortização"]
x.CD_CONTA.value_counts()

# para ajudar a debugar

def test(dados, cvm, conta, ano):
    df = dados.loc[(dados.CD_CVM == cvm) & (dados.DT_FIM_EXERC.dt.year == ano) & (dados.CD_CONTA == conta)]
    return df
"""

################################
# outras funções


nome_arquivos = ['dados/'+nome+'.zip' for nome in nome_arquivos]

setor_i = pd.DataFrame(dict(Setor_Atividade=filtro_setor, setor=range(1,len(filtro_setor)+1)))
dados_cvm = pd.read_csv('dados_companhia.csv', sep=';', encoding="mbcs", header=0)
dados_cvm = dados_cvm.loc[dados_cvm.Codigo_Negociacao.str[-2:] != "3B"]
dados_cvm = dados_cvm.merge(setor_i, how='left', on='Setor_Atividade')
dados_cvm['setor'] = dados_cvm['setor'].fillna(0).astype(int)

dados_cvm_sub = dados_cvm[['Codigo_CVM','setor']]
demostrativos = ['BPA','BPP','DRE','DFC_MD','DFC_MI']
demo_chaves = [(x[:3],x) for x in demostrativos]

def obter_tabela(d, ano):
    con = []
    myzip = ZipFile("dados/" + d + "_cia_aberta_" + ano + ".zip", 'r')
    for i in demostrativos:
        data = myzip.open(d + "_cia_aberta_" + i + "_con_" + ano + ".csv")
        con.append(pd.read_csv(data, sep=";", encoding="mbcs", header=0))

    ind = []
    for i in demostrativos:
        data = myzip.open(d + "_cia_aberta_" + i + "_ind_" + ano + ".csv")
        ind.append(pd.read_csv(data, sep=";", encoding="mbcs", header=0))
    myzip.close()

    con = pd.concat(con, keys=demo_chaves, names=['demo2','demo1'])
    ind = pd.concat(ind, keys=demo_chaves, names=['demo2','demo1'])

    df = pd.concat([con, ind.loc[~ind['CD_CVM'].isin(con['CD_CVM'])]]).reset_index()

    df = df.loc[df['ORDEM_EXERC'] == "ÚLTIMO"]
    df['demo1'] = d.upper()
    df = df.merge(dados_cvm_sub, left_on = 'CD_CVM', right_on = 'Codigo_CVM')

    df['VL_CONTA'] = df['VL_CONTA'].mask(df['ESCALA_MOEDA'] == "MIL", df['VL_CONTA']*1000)
    df['DT_FIM_EXERC'] = pd.to_datetime(df['DT_FIM_EXERC'], format="%Y-%m-%d")
    df['DT_INI_EXERC'] = pd.to_datetime(df['DT_INI_EXERC'], format="%Y-%m-%d")
    df_g = df.groupby(['demo1','demo2','CD_CVM','CD_CONTA','DT_FIM_EXERC','DT_INI_EXERC'], dropna=False)
    return df_g.agg({'setor':'first', 'DS_CONTA': 'first', 'VL_CONTA': 'first'})


def filtrar(dados, index, tmp, unicos, nome, op):
    unicos = pd.DataFrame({'DS_CONTA': unicos, 'manter': tmp})

    dadosk = dados.merge(unicos, on="DS_CONTA", how="left").reset_index()
    dadosk['manter'].fillna(False, inplace=True)
    dadosk.loc[dadosk.manter & index, 'CD_CONTA'] = nome

    dadosk.loc[dadosk.manter & index & op(dadosk.VL_CONTA, 0), 'VL_CONTA'] = 0
    dadosk.drop(columns=['index','manter'], inplace=True)
    return dadosk


def obter_arquivo(url, old):
    arq = pd.read_html(url, parse_dates = ["Last modified"], attrs = {'id': 'indexlist'})[0]
    arq = arq.drop(columns = ['Unnamed: 0', 'Size', 'Description']).dropna(axis='rows')
    arq = arq.merge(old, how="left", on=["Name"], suffixes= ['','_i'])
    arq['diferente'] = (arq["Last modified"] > arq["Last modified_i"]) | pd.isnull(arq["Last modified_i"])
    arq['url'] = url
    return arq


def atualizar_bancos(apenasUltimo = True):
    # pegar codigo dos conglomerados
    dados_bancos = pd.read_csv("dados_bco.csv", sep=';', encoding="mbcs")
    dados_bancos_a2014 = dados_bancos[['Codigo_CVM','CodIF_F']].dropna()
    dados_bancos_a2014['CodIF_F'] = dados_bancos_a2014['CodIF_F'].astype(int)
    dados_bancos_d2014 = dados_bancos[['Codigo_CVM','CodIF_P']]
    ano_referencia = pd.Timestamp(year=2015, month=3, day=1)

    # obter datas
    anos = requests.get("https://www3.bcb.gov.br/ifdata/rest/relatorios").json()
    anos = pd.DataFrame(anos)['dt'].astype(str).to_frame()
    anos['dtdt'] = pd.to_datetime(anos.dt, format="%Y%m")

    if apenasUltimo and exists("dados/IFDATA.zip"):
        anos = anos.iloc[-1]
    else:
        apenasUltimo = False
        anos = anos.loc[anos.dtdt >= pd.Timestamp(year=2009, month=3, day=1)]
    
    # baixar arquivo de cada trimestre
    dado_final = []
    for index, contents in anos.iterrows():
        dt = contents['dt']
        if contents.dtdt.month == 3:
            print("Baixando dados Bancos " + str(contents.dtdt.year))

        url="https://www3.bcb.gov.br/ifdata/rest/arquivos?nomeArquivo="+dt+"/dados"+dt+"_1.json"
        dado = requests.get(url).json()
        dado2 = pd.json_normalize(dado, ['values','v'], ['id',['id','e']])

        dado2 = dado2.merge(fund_banco, left_on='i', right_on='NomeColuna')
        dado2['id.e'] = dado2['id.e'].astype(int)

        if contents.dtdt >= ano_referencia:
            dado2 = dado2.merge(dados_bancos_d2014, left_on='id.e', right_on='CodIF_P')
        else:
            dado2 = dado2.merge(dados_bancos_a2014, left_on='id.e', right_on='CodIF_F')
        
        dado2['data'] = dt
        dado2 = dado2[['data','nome_conta','Codigo_CVM','v']]
        dado_final.append(dado2)
    
    dado_final2 = pd.concat(dado_final)

    if apenasUltimo:
        dado_final2 = juntar_ultimo("dados/IFDATA.zip", dado_final2, cname = 'data')

    dado_final2.to_csv("dados/IFDATA.zip", sep=';', encoding="mbcs", index=False)
    pass


def juntar_ultimo(old, new, cname = 'DT_FIM_EXERC'):
    dado_old = pd.read_csv(old, sep=';', encoding="mbcs")
    dado_old = dado_old.loc[~dado_old[cname].isin(new[cname])]
    return pd.concat([dado_old, new])
