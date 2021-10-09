import dash
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import numpy as np
import pandas as pd
from funcoes import dados_cvm, nome_arquivos
from estilo import cols_table, cols_graf, estilo_cabecalho, estilo_dados, cor

# importar dados
dados = [pd.read_csv(f, sep=';', encoding="mbcs", header=0, parse_dates=["DT_FIM_EXERC"]) for f in nome_arquivos]
dados = [df.sort_values(['demo1','CD_CVM','DT_FIM_EXERC']) for df in dados]
dados = [df.assign(DT_MA=df['DT_FIM_EXERC'].dt.strftime('%m/%Y')) for df in dados]

codigo = dados_cvm['Codigo_Negociacao'].str[:4].fillna('XXXX') + " - " + dados_cvm['Nome_Empresarial']


# formatar graficos
fg1 = {'xaxis_title': "", 'yaxis_title': "", 'margin': {'t': 50, 'b': 50}, 'plot_bgcolor': cor['graf'], \
        'paper_bgcolor': cor['fundo'], 'font_color': cor['fonte'], 'legend_title': 'Fundamentos', 'hovermode': 'x'}

fg2 = {'linecolor': cor['fonte'], 'mirror': True, 'gridcolor': cor['grid']}


fg3 = {'rangeselector': 
    {'buttons': [
        dict(step="all", label="Tudo"),
        dict(count=10, label="10 anos", step="year", stepmode="backward"),
        dict(count=5, label="5 anos", step="year", stepmode="backward")
    ], 'bgcolor': cor['busca']}
}
fg3.update(fg2)


urlb3 = "http://bvmf.bmfbovespa.com.br/cias-listadas/empresas-listadas/ResumoEmpresaPrincipal.aspx?codigoCvm={}&idioma=pt-br"
urlsi = "https://statusinvest.com.br/acoes/"

sitetv = """<html><head></head><body>
<!-- TradingView Widget BEGIN -->
<script type="text/javascript" src="https://s3.amazonaws.com/tradingview/tv.js"></script>
<script type="text/javascript">
  new TradingView.widget({{
	"container_id": "tv-adv-widget-home",
	"width": "100%",
	"height": "550px",
	"symbol": "BMFBOVESPA:{}",
	"interval": "W",
	"timezone": "America/Sao_Paulo",
	"theme": "dark",
	"style": "3",
	"withdateranges": true,
	"details": true,
	"allow_symbol_change": true,
	"hideideas": true,
	"show_popup_button": false,
	"editablewatchlist": true,
	"customer": "bovespa",
	"locale": "br"
  }});
</script>
<!-- TradingView Widget END -->
</body></html>"""


app = dash.Dash()
app.title = "Fundamentos"

app.layout = html.Div([
    html.H1('Fundamentos', style = {'text-align': 'center'}),
    html.Div([
        html.Div(dcc.Dropdown(
            id="cod_acao",
            options=[{"label": x, "value": "{:d}_{:d}".format(y,z)} for (x,y,z) in zip(codigo, dados_cvm.Codigo_CVM, dados_cvm.setor)],
            value="5410_0",
            clearable=False,
            style={'backgroundColor': cor['busca'], 'color': cor['fonte']}), 
        style={'width': '50%', 'display': 'inline-block'}),
        dcc.RadioItems(
            id="itr_dfp",
            options=[{"label": "Anual", "value": 1}, {"label": "Trimestral", "value": 2}],
            value=1,
            labelStyle={'display': 'inline-block', 'margin-left': '15px', 'font-size': 'larger', 'font-weight': 'bold', 'cursor': 'pointer'}
        )
    ], style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center'}),
    html.Br(),
    html.Table([
        html.Tr(html.Td(id='nome', style = {'font-weight': 'bold', 'font-size': '125%'}, colSpan = 2)),
        html.Tr([html.Td(id='codigo'), html.Td(id='cnpj')]),
        html.Tr([html.Td(id='setor'), html.Td([dcc.Link('Site RI', id='pagri', href='/', target='_blank'), " | ", 
                                               dcc.Link('Site B3', id='pagb3', href='/', target='_blank'), " | ",
                                               dcc.Link('StatusInvest', id='pagsi', href='/', target='_blank')])
                ]),
        html.Tr(html.Td(id='descricao', colSpan = 2)),
    ], style = {'width': '50%', 'margin-left': 'auto', 'margin-right': 'auto', 'table-layout': 'fixed'}),
    html.Br(),
    html.Div(id='tabela_dados'),
    dcc.Graph(id ='grafico0'),
    dcc.Graph(id ='grafico1'),
    dcc.Graph(id ='grafico2'),
    html.Iframe(id = 'tvgraf', srcDoc='', style={'width': '80%', 'height': '600px', 'display': 'block', 
                                                'margin-left': 'auto', 'margin-right': 'auto', 'border-style':'none'})
])




@app.callback(
    Output('nome', 'children'),
    Output('codigo', 'children'),
    Output('cnpj', 'children'),
    Output('setor', 'children'),
    Output('descricao', 'children'),
    Output('pagri', 'href'),
    Output('pagb3', 'href'),
    Output('tvgraf', 'srcDoc'),
    Output('pagsi', 'href'),
    
    Input('cod_acao','value'))
def obter_descricao(cod_cvm):
    dados_sel = dados_cvm.loc[dados_cvm.Codigo_CVM == int(cod_cvm.split("_")[0])]
    cod_url = dados_sel.Codigo_Negociacao.values[0].split(" ")[0]
    return [dados_sel.Nome_Empresarial, dados_sel.Codigo_Negociacao, 'CNPJ: ' + dados_sel.CNPJ_Companhia, dados_sel.Setor_Atividade,
            dados_sel.Descricao_Atividade, dados_sel.Pagina_Web.values[0], 
            urlb3.format(dados_sel.Codigo_CVM.values[0]), sitetv.format(cod_url), urlsi+cod_url.lower(), ]


@app.callback(
    Output('grafico0','figure'),
    Output('grafico1','figure'),
    Output('grafico2','figure'),
    Output('tabela_dados', 'children'),
    Input('cod_acao', 'value'),
    Input('itr_dfp', 'value'))
def obter_valores(cod_cvm, itr_dfp):
    cod_cvm = cod_cvm.split("_")
    setor = int(cod_cvm[1])
    sel0 = dados[setor]
    if itr_dfp == 1:
        sel = sel0.loc[(sel0.demo1 == "DFP") & (sel0.CD_CVM == int(cod_cvm[0]))]
    else:
        sel = sel0.loc[(sel0.demo1 == "ITR") & (sel0.CD_CVM == int(cod_cvm[0]))]

    figuras = []
    for i in range(3):
        fig = px.line(sel, x='DT_FIM_EXERC', y=cols_graf[setor][i])
        fig.update_layout(fg1)
        fig.update_xaxes(fg3)
        fig.update_yaxes(fg2)
        figuras.append(fig)
    
    figuras[0].update_traces(mode="markers+lines", hovertemplate = '%{y:.3s}')
    figuras[2].update_traces(mode="markers+lines", hovertemplate = '%{y:.3s}')
    figuras[1].update_traces(mode="markers+lines", hovertemplate = '%{y:.2%}')

    # impedir que os limites desses gráfico fiquem muito grande
    min_por = max(-5, np.nanmin(sel[cols_graf[setor][1]].values))
    max_por = min(5, np.nanmax(sel[cols_graf[setor][1]].values))
    range_por = (max_por - min_por)*0.05
    figuras[1].update_yaxes(range=[min_por-range_por, max_por+range_por], tickformat = ".0%")
  

    tabela = dash_table.DataTable(
        id='tab_dados',
        columns = cols_table[setor],
        data = sel.to_dict(orient='records'),
        style_cell={'textAlign': 'center', 'backgroundColor': cor['fundo'], 'border': '1px solid '+cor['grid'],
                    'minWidth': 70, 'maxWidth': 120},
        style_header = {'backgroundColor': cor['verde'], 'fontWeight': 'bold'},
        style_header_conditional = estilo_cabecalho,
        style_data_conditional = estilo_dados,
    )

    return figuras + [tabela]


if __name__ == '__main__':
    app.run_server(debug=True)
