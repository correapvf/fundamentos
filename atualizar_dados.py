from os.path import exists
from os import makedirs
import argparse
import time
import requests
import numpy as np
import pandas as pd
from funcoes import obter_arquivo, obter_tabela, atualizar_bancos, juntar_ultimo, nome_arquivos, funcoes_valores, funcoes_fundamentos

def atualizar(apenasUltimo):
    start_time = time.time()

    if not exists('dados'):
        os.makedirs('dados')

    itr_url = "http://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/"
    dfp_url = "http://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/"

    # verificar ultimas atualizacoes da cvm
    if exists('dados/metadados.zip'):
        old = pd.read_csv("dados/metadados.zip", parse_dates=["Last modified"])
    else:
        arq1 = pd.read_html(itr_url, parse_dates = ["Last modified"], attrs = {'id': 'indexlist'})[0]
        arq2 = pd.read_html(dfp_url, parse_dates = ["Last modified"], attrs = {'id': 'indexlist'})[0]
        old = pd.concat([arq1, arq2])
        old = old.drop(columns = ['Unnamed: 0', 'Size', 'Description']).dropna(axis='rows')
        old["Last modified"] = old["Last modified"] - pd.Timedelta(1, 'days')
        apenasUltimo = False

    # verificar ultima atualizacao do IFDATA
    if exists("dados/metadados_banco.txt"):
        with open("dados/metadados_banco.txt", 'r') as f:
            banco_old = f.read()
    else:
        banco_old = "xxxx"
        apenasUltimo = False

    # veriicar se todos os arquivos estao presentes
    arq_check = all([exists(nome) for nome in nome_arquivos])
    if not arq_check:
        apenasUltimo = False


    old = old.groupby(old['Name'].str[:3])
    itr = obter_arquivo(itr_url, old.get_group("itr"))
    dfp = obter_arquivo(dfp_url, old.get_group("dfp"))

    # atualizar metadados
    if apenasUltimo:
        arquivos0 = pd.concat([itr.iloc[:-1], dfp.iloc[:-1]])
        arquivos0.drop(columns = ['Last modified'], inplace = True)
        arquivos0.rename(columns = {'Last modified_i':'Last modified'}, inplace = True)

        arquivos = pd.DataFrame([itr.iloc[-1], dfp.iloc[-1]])
        arquivos0 = pd.concat([arquivos0, arquivos])
        arquivos0[['Name','Last modified']].to_csv('dados/metadados.zip', index=False)
    else:
        arquivos = pd.concat([itr, dfp])
        arquivos[['Name','Last modified']].to_csv('dados/metadados.zip', index=False)

    arquivos2 = arquivos.loc[arquivos.diferente]

    # download dos arquivos se precisam ser atualizados
    for index, contents in arquivos2.iterrows():
        print('Baixando ' + contents['Name'])
        r = requests.get(contents['url'] + contents['Name'])
        with open("dados/" + contents['Name'], 'wb') as output_file:
            output_file.write(r.content)


    # download dos arquivos dos bancos
    url_bancos = "https://dadosabertos.bcb.gov.br/dataset/ifdata---dados-selecionados-de-instituies-financeiras"
    df_bancos = pd.read_html(url_bancos)[0]
    bco = df_bancos.Valor.loc[df_bancos.Campo == "Última Atualização"].values[0]

    if bco != banco_old:
        atualizar_bancos(apenasUltimo)
        with open("dados/metadados_banco.txt", 'w') as f:
            f.write(bco)



    ######################################
    # Refazer base de dados se necessario
    if (arquivos2.shape[0] > 0) or (bco != banco_old) or not arq_check:
        arquivos['tipo'] = arquivos['Name'].str.split('_').str[0]
        arquivos['ano'] = arquivos['Name'].str.split('_').str[-1].str.split('.').str[0]
        dados = []
        for index, contents in arquivos.iterrows():
            print("Abrindo " + contents['Name'])
            dados.append(obter_tabela(contents['tipo'], contents['ano']))

        
        print("Salvando dados")
        dados = pd.concat(dados).reset_index()
        colunas = ['demo1','demo2','CD_CVM','CD_CONTA','DT_FIM_EXERC','DT_INI_EXERC']

        # remover possíveis duplicadas (talvez seja desnecessário)
        #dados.sort_values(colunas, inplace=True)
        #dados = dados.groupby(colunas, dropna=False).last().reset_index()

        # obter periodo do exercício, em meses
        index = dados['DT_INI_EXERC'].isna()
        dados.loc[index, 'DT_INI_EXERC'] = dados.loc[index, 'DT_FIM_EXERC']
        dados['periodo'] = ((dados['DT_FIM_EXERC'] - dados['DT_INI_EXERC']) / np.timedelta64(1, 'M')).round().astype(int)


        # arrumar DRE
        # manter apenas os valores referentes ao ultimo trimstre
        dre3 = dados.loc[(dados.demo2 == "DRE") & (dados.demo1 == "ITR") & (dados['periodo'] == 3)]

        # calcular o valor do 4o trimestre baseado na dfp
        dre9 = dados.loc[(dados.demo2 == "DRE") & (dados.demo1 == "ITR") & (dados['periodo'] == 9)].copy()
        dre12 = dados.loc[(dados.demo2 == "DRE") & (dados.demo1 == "DFP") & (dados['periodo'] == 12)]

        dre9['DT_FIM_EXERC'] = dre9['DT_FIM_EXERC'] + pd.offsets.MonthEnd(3)
        dre12n = dre12.merge(dre9, on=colunas[2:5], suffixes=['_i','']).reset_index()
        dre12n['VL_CONTA'] = dre12n['VL_CONTA_i'] - dre12n['VL_CONTA']

        # arrumar DFC
        dfc369 = dados.loc[(dados.demo2 == "DFC") & (dados.demo1 == "ITR") & dados['periodo'].isin([3, 6, 9])].copy()
        dfc12 = dados.loc[(dados.demo2 == "DFC") & (dados.demo1 == "DFP") & (dados['periodo'] == 12)]
        dfc = pd.concat([dfc369, dfc12])

        dfc369['DT_FIM_EXERC'] = dfc369['DT_FIM_EXERC'] + pd.offsets.MonthEnd(3)
        dfc = dfc.merge(dfc369, on=colunas[2:5], suffixes=['_i','']).reset_index()
        dfc['VL_CONTA'] = dfc['VL_CONTA_i'] - dfc['VL_CONTA']

        dfc3 = dados.loc[(dados.demo2 == "DFC") & (dados.demo1 == "ITR") & (dados['periodo'] == 3)]

        # arrumar BPP
        bpp1 = dados.loc[(dados.demo2 == "BPP") & (dados.demo1 == "DFP")].copy()
        bpp1['demo1'] = "ITR"
        minbpp = dados.loc[(dados.demo2 == "BPP") & (dados.demo1 == "ITR")].DT_FIM_EXERC.min()
        bpp1 = bpp1.loc[bpp1['DT_FIM_EXERC'] >= minbpp]
        bpp = dados.loc[(dados.demo2 == "BPP")]

        # arrumar BPA
        bpa1 = dados.loc[(dados.demo2 == "BPA") & (dados.demo1 == "DFP")].copy()
        bpa1['demo1'] = "ITR"
        minbpa = dados.loc[(dados.demo2 == "BPA") & (dados.demo1 == "ITR")].DT_FIM_EXERC.min()
        bpa1 = bpa1.loc[bpa1['DT_FIM_EXERC'] >= minbpa]
        bpa = dados.loc[(dados.demo2 == "BPA")]

        # juntar tudo
        dados = pd.concat([bpa, bpa1, bpp, bpp1, dre3, dre12n, dre12, dfc3, dfc, dfc12], join = 'inner')
        dados.drop(columns=['DT_INI_EXERC','periodo'], inplace=True)
        dados['DS_CONTA'].fillna("", inplace=True)
        dados.reset_index(inplace=True, drop=True)

        # calcular CAPEX e proventos
        for funcao in funcoes_fundamentos:
            dados = funcao(dados)

        # debug
        #dados2.to_pickle('dados2_debug')
        #dados2 = pd.read_pickle('dados2_debug')

        # separar por setor e calcular fundamentos
        dados = dados.groupby('setor')
        dados_final = [funcao(dados.get_group(i)) for i, funcao in enumerate(funcoes_valores)]
            

        if apenasUltimo:
            dados_final = [juntar_ultimo(old, new) for (old, new) in zip(nome_arquivos, dados_final)]

        for (new, file) in zip(dados_final, nome_arquivos):
            new.to_csv(file, sep=';', encoding="mbcs", index=False)

    print("Finalizado - %.1f segundos" % (time.time() - start_time))



parser = argparse.ArgumentParser(description="Atualiza os arquivos lançados pela CVM e BC")
parser.add_argument("--ultimo", default=False, action="store_true",
                    help="Atualiza apenas o ultimo arquivo lançado")
args = parser.parse_args()

if __name__ == '__main__':
    atualizar(args.ultimo)
