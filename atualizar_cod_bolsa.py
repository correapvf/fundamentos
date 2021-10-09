import requests
import pandas as pd
from bs4 import BeautifulSoup

url = "http://bvmf.bmfbovespa.com.br/pt-br/mercados/acoes/empresas/ExecutaAcaoConsultaInfoEmp.asp?CodCVM="

# tentar atualizar codigos da bolsa
dados_cvm = pd.read_csv('dados_companhia.csv', sep=';', encoding="mbcs", header=0)
index_cvm = dados_cvm['Codigo_Negociacao'].isna()
dados_cvm2 = dados_cvm.loc[index_cvm].copy()

novo_cod = dados_cvm2['Codigo_Negociacao'].copy()
n = 0
for index, contents in dados_cvm2.iterrows():
    print("Tentado obter da " + contents.Nome_Empresarial)
    page = requests.get(url + str(contents.Codigo_CVM))
    soup = BeautifulSoup(page.content, "html.parser")
    cod = soup.find_all("a", class_="LinkCodNeg")

    if cod: # if not empty
        cods = [c.text for c in cod]
        if cods != ['']:
            x = list(set(cods))
            xn = [int(c[4:]) for c in x]
            xn.sort()
            x = [x[0] + str(c) for c in xn]
            novo_cod.loc[index] = ' '.join(x)
            n += 1


if n > 0:
    dados_cvm2['Codigo_Negociacao'] = novo_cod
    dados_cvm = pd.concat([dados_cvm.loc[~index_cvm], dados_cvm2])
    dados_cvm.to_csv('dados_companhia.csv', sep=';', encoding="mbcs", index=False)
    print(str(n) + " novos códigos da bolsa foram atualizados")
else:
    print("Nenhum novo código da bolsa foi encontrado")
