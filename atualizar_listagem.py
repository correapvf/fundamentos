from os.path import exists
from zipfile import ZipFile
import requests
import pandas as pd

print("Atualizando empresas com cadastro na CVM")

# obter dados da cvm
url = "http://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/"
arquivo = pd.read_html(url, parse_dates = ["Last modified"], attrs = {'id': 'indexlist'})
arquivo = arquivo[0]['Name']
arquivo = arquivo.dropna()
arquivo = arquivo.iloc[-1]

r = requests.get(url + arquivo)
with open("dados/" + arquivo, 'wb') as output_file:
    output_file.write(r.content)

ano = arquivo.rsplit("_", 1)[1].split(".")[0]
myzip = ZipFile("dados/" + arquivo, 'r')
data1 = myzip.open("fca_cia_aberta_geral_" + ano + ".csv")
data2 = myzip.open("fca_cia_aberta_valor_mobiliario_" + ano + ".csv")
myzip.close()

data1 = pd.read_csv(data1, sep=";", encoding="mbcs", header=0)
data2 = pd.read_csv(data2, sep=";", encoding="mbcs", header=0)

# filtrar e mesclar os dados
df1 = data1[['CNPJ_Companhia', 'Nome_Empresarial','Codigo_CVM','Setor_Atividade','Descricao_Atividade','Pagina_Web']]

df2 = data2[['CNPJ_Companhia','Valor_Mobiliario','Codigo_Negociacao','Mercado','Data_Fim_Negociacao','Data_Fim_Listagem']]
df2 = df2.loc[df2.Valor_Mobiliario.isin(['Ações Ordinárias','Ações Preferenciais','Units']) & 
                ((df2.Mercado == "Bolsa") | (df2.Mercado.isna())) & 
                df2.Data_Fim_Negociacao.isna() & df2.Data_Fim_Listagem.isna()]
df2['Codigo_Negociacao'] = df2['Codigo_Negociacao'].str.upper().astype(str)
df2 = df2.groupby(['CNPJ_Companhia'])['Codigo_Negociacao'].apply(' '.join).reset_index()

dados = df1.merge(df2, on="CNPJ_Companhia")
dados.Nome_Empresarial = dados.Nome_Empresarial.str.replace(' S.A.', '')
dados.Nome_Empresarial = dados.Nome_Empresarial.str.replace(' S/A', '')
dados.Nome_Empresarial = dados.Nome_Empresarial.str.replace('BCO', 'BANCO')
dados = dados[['Codigo_CVM','Codigo_Negociacao','Nome_Empresarial','Setor_Atividade',
                'CNPJ_Companhia','Pagina_Web','Descricao_Atividade']]

# salvar arquivo
if exists('dados_companhia.csv'):
    dados_old = pd.read_csv('dados_companhia.csv', sep=';', encoding="mbcs", header=0)
    dados_new = dados.loc[~dados.Codigo_CVM.isin(dados_old.Codigo_CVM)]
    nrows = dados_new.shape[0]
    if nrows == 0:
        print("Nenhum novo registro encontrado.")
    else:
        dados_new.to_csv('dados_companhia.csv', sep=';', encoding="mbcs", header=False, index=False, mode="a")
        print("'dados_companhia.csv' atualizado com " + str(nrows) + " registros.")
else:
    dados.to_csv('dados_companhia.csv', sep=';', encoding="mbcs", index=False)
    print("Arquivo 'dados_companhia.csv' Salvo.")


#############################
# obter as listagens de bancos
print("Atualizando cadastro dos bancos")

# Pegar Bancos com código na bolsa
dados_bancos = pd.read_csv('dados_companhia.csv', sep=';', encoding="mbcs", header=0)
dados_bancos = dados_bancos.loc[(dados_bancos.Codigo_Negociacao.str[-2:] != "3B") & (dados_bancos.Setor_Atividade == "Bancos"), \
    ['Codigo_CVM','Nome_Empresarial','CNPJ_Companhia']].copy()
dados_bancos['CNPJ_Companhia'] = dados_bancos.CNPJ_Companhia.str.split('/').str[0].str.replace('.','',regex=False)


# obter códigos dos banco na banco central
da = pd.Timestamp.now()
dataref = "{:4d}{:02d}".format(da.year, (da.month//3)*3)

url = "https://olinda.bcb.gov.br/olinda/servico/IFDATA/versao/v1/odata/IfDataCadastro(AnoMes=@AnoMes)?@AnoMes=" \
    + dataref +"&$filter=Situacao%20eq%20'A'&$format=json&$select=CodInst,CodConglomeradoFinanceiro,CodConglomeradoPrudencial"

response = requests.get(url).json()
cod_bancos = pd.DataFrame(response['value'])

# mesclar e salvar as informcoes
dados_bancos = dados_bancos.merge(cod_bancos, left_on='CNPJ_Companhia', right_on='CodInst')
dados_bancos['CodIF_F'] = dados_bancos.CodConglomeradoFinanceiro.str[3:]
dados_bancos['CodIF_P'] = dados_bancos.CodConglomeradoPrudencial.str.replace('C','100',regex=False)
dados_bancos.drop(columns=['CodInst','CodConglomeradoFinanceiro','CodConglomeradoPrudencial'], inplace=True)

if exists('dados_bco.csv'):
    dados_bancos_old = pd.read_csv('dados_bco.csv', sep=';', encoding="mbcs", header=0)
    dados_bancos_new = dados_bancos.loc[~dados_bancos.Codigo_CVM.isin(dados_bancos_old.Codigo_CVM)]
    nrows = dados_bancos_new.shape[0]
    if nrows > 0:
        dados_bancos_new.to_csv('dados_bco.csv', sep=';', encoding="mbcs", header=False, index=False, mode="a")
        print("'dados_bco.csv' atualizado com " + str(nrows) + " registros.")
else:
    dados_bancos.to_csv('dados_bco.csv', sep=';', encoding="mbcs", index=False)
    print("Arquivo 'dados_bco.csv' Salvo.")

print("Finalizado")
