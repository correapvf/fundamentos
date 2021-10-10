## fundamentos
Obter fundamentos das empresas listadas na B3 a partir da CVM e do IFdata

### Instalar dependências
```
python -m pip install --upgrade pip
pip install dash pandas requests unidecode nltk bs4 lxml

python
import nltk
nltk.download('stopwords')
nltk.download('rslp')
```

### Primeiros passos
- Baixar arquivos da CVM: `python atualizar_dados.py`
- Iniciar servidor do site: `python app.py`
- Acesse o site pelo navegador - http://127.0.0.1:8050/

### Configuração
Editar arquivos `funcoes.py` para alterar os fundamentos que são obtidos e `estilo.py` para alterar como os fundamentos são exibidos no site.

`atualizar_listagem.py` vai atualizar os arquivos *dados_companhia.csv* e
*dados_bco.csv* com novas possíveis empresas e bancos.
`atualizar_cod_bolsa.py` vai tentar buscar os códigos de negociação ausentes no site da B3.

### Aviso
As informações são coletadas de fontes públicas.
Erros podem ocorrer ao processar os dados coletados.
Não me responsabilizo por decisões tomados a partir da análise dessas informações.