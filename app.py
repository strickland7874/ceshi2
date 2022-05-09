import base64
import io
import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table
import pandas as pd
import dash_bootstrap_components as dbc
import numpy as np
import plotly.express as px
import dash_daq as daq
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div([
    html.H1('Theis配线法求解水文地质参数'),
    #用户输入组件 
    daq.NumericInput(  
        id='our-numeric-input',
        label='输入观测孔于抽水孔距离r/m',
        size=200,
        min=0,
        max=100000,
        value=0,
    ),
    html.Div(id='numeric-input-result'),
    daq.NumericInput(
        id='our-Q-input',
        label='抽水孔定流量Qm3/min',
        size=200,
        min=0,
        max=10000,
        value=0,
    ),
    html.Div(id='numeric-Q-result'),

    # 上传组件
    dcc.Upload(
        id='datatable-upload',
        children=html.Div([
            '拖放xlsx或csv文件到此(注：双列文档，第一列为t第二列为s)，或 ',
            html.A('选择文件')
        ]),
        style={
            'width': '100%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
        },
    ),
    dash_table.DataTable(id='datatable-upload-container', editable=True),
    dcc.Graph(id='datatable-upload-graph'),
    #设置两个曲线平移滑块
    dbc.Col([
        dbc.Label('上下平移:'),
        dcc.Slider(id='perc_pov_shang_slider',
                   min=-3,
                   max=3,
                   step=0.01,
                   included=False,
                   value=0,
                   marks={-3:  {'label': '-3'}, 
                          0:  {'label': '0'},
                          3:  {'label': '3'}}), 

        ], lg=5),
           
    dbc.Col([
        dbc.Label('左右平移:'),
        dcc.Slider(id='perc_pov_zuo_slider',
                   min=-5, 
                   max=5,
                   step=0.01,
                   included=False,
                   value=0,
                   marks={-5:  {'label': '-5'}, 
                          0:  {'label': '0'},
                          5:  {'label': '5'}}),
                 
        ], lg=5),
    html.Div(id='numeric-output-result'),
    html.Div(id='numeric-S-result'),

])


def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    if 'csv' in filename:
        return pd.read_csv(
            io.StringIO(decoded.decode('utf-8')))
    elif 'xls' in filename:
        return pd.read_excel(io.BytesIO(decoded))


@app.callback(Output('datatable-upload-container', 'data'),
              Output('datatable-upload-container', 'columns'),
              Input('datatable-upload', 'contents'),
              State('datatable-upload', 'filename'))

def update_output(contents, filename):
    #将文档内容传入表格
    if contents is None:
        return [{}], []
    df = parse_contents(contents, filename)
    
    return df.to_dict('records'), [{"name": i, "id": i} for i in df.columns]

@app.callback(
    Output('numeric-input-result', 'children'),
    Input('our-numeric-input', 'value')
)
def update_output(value):
    return f'输入值是 {value}/m'


@app.callback(
    Output('numeric-Q-result', 'children'),
    Input('our-Q-input', 'value')
)
def update_output(value):
    return f'输入值是 {value}m3/min'


@app.callback(Output('datatable-upload-graph', 'figure'),
            
              Input('datatable-upload-container','data'),
              Input('perc_pov_zuo_slider','value'),
              Input('perc_pov_shang_slider','value'),
              Input('our-numeric-input', 'value')
            )
def display_graph(rows,input_zuo_value,input_shang_value,input_numeric_value):
   #表格数据给图表
    df = pd.DataFrame(rows)

    df = df.apply(lambda x:(x/input_numeric_value**2)+input_zuo_value if x.name in ['t'] else x)
    df = df.apply(lambda y:y+input_shang_value if y.name in ['s'] else y)
    #散点图的平移
    if (df.empty or len(df.columns) < 1):
        return {
                 'data':[{
                    
                    'x': [],
                    'y': [],
                    'type': 'scatter',
                    'mode':'markers',
                }],

        }
        
    return { 
                'data':[{   
                'x': df[df.columns[0]],
                'y': df[df.columns[1]],
                'type': 'scatter',
                'mode':'markers',
                }],

        }

@app.callback(Output('numeric-output-result', 'children'),
              Input('perc_pov_shang_slider','value'),
              Input('perc_pov_zuo_slider','value'),
              Input('our-Q-input', 'value'))

def update_output(input_shang_value,input_Q_value,input_zuo_value):
    c=input_shang_value*input_Q_value/(4*np.pi)
    d=4*c*input_zuo_value
    return f'求得导水系数T为： {c},储水系数为：{d}'


if __name__ == '__main__':
    app.run_server(debug=True)
