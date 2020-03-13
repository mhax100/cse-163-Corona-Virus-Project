# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import requests
import geopandas
import pandas as pd
import math
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime as dt



def get_data(url, file_name):
    r = requests.get(url, allow_redirects=True)
    with open(file_name, 'wb') as f:
        f.write(r.content)


def geo_convert(file_name):
    frame = pd.read_csv(file_name)
    frame.fillna(0)
    frame = geopandas.GeoDataFrame(
        frame, geometry=geopandas.points_from_xy(frame.Long, frame.Lat))
    return frame


def log_unless_zero(input):
    if (input == 0):
        return 0
    else:
        return math.log(input)


def geo_melter(df, value_col):
    recent_date = geo_confirmed.columns[-2]
    return pd.melt(df, id_vars=['Province/State', 'Country/Region',
                                'Lat','Long', 'geometry'],
                   value_vars=df.loc[:,'1/22/20':recent_date].columns,
                   var_name='date', value_name=value_col)


url_confirmed = ('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/'
                 'master/csse_covid_19_data/csse_covid_19_time_series/'
                 'time_series_19-covid-Confirmed.csv')

url_deaths = ('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/'
              'master/csse_covid_19_data/csse_covid_19_time_series/'
              'time_series_19-covid-Deaths.csv')

url_recovered = ('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/'
                 'master/csse_covid_19_data/csse_covid_19_time_series/'
                 'time_series_19-covid-Recovered.csv')

get_data(url_confirmed, 'covid19_confirmed.csv')
get_data(url_deaths, 'covid19_deaths.csv')
get_data(url_recovered, 'covid19_recovered.csv')

geo_confirmed = geo_convert('covid19_confirmed.csv')
geo_deaths = geo_convert('covid19_deaths.csv')
geo_recovered = geo_convert('covid19_recovered.csv')

geo_confirmed_melted = geo_melter(geo_confirmed, 'Confirmed')
geo_deaths_melted = geo_melter(geo_deaths, 'Deaths')
geo_recovered_melted = geo_melter(geo_recovered, 'Recovered')

cols_to_use = geo_deaths_melted.columns.difference(geo_confirmed_melted.columns)
geo_master = pd.merge(geo_confirmed_melted, geo_deaths_melted[cols_to_use], left_index=True, right_index=True, how='outer')
cols_to_use = geo_recovered_melted.columns.difference(geo_master.columns)
geo_master = pd.merge(geo_master, geo_recovered_melted[cols_to_use], left_index=True, right_index=True, how='outer')

geo_master['Confirmed_Size'] = geo_master.apply(lambda x: log_unless_zero(x['Confirmed']), axis=1)
geo_master['Deaths_Color'] = geo_master.apply(lambda x: log_unless_zero(x['Deaths']), axis=1)
geo_master.loc[geo_master['Province/State'].isnull(), 'Province/State'] = geo_master['Country/Region']

geo_master['text'] = (', Confirmed: ' + geo_master['Confirmed'].astype(str)
                      + ', Deaths: ' + geo_master['Deaths'].astype(str)
                      + ', Recovered: ' + geo_master['Recovered'].astype(str))

geo_master['date'] = pd.to_datetime(geo_master['date'], format='%m/%d/%y')

scl = [[0, '#8c96c6'],[0.33, '#8c6bb1'],[0.66, '#88419d'],[1.0, '#6e016b']]\


app = dash.Dash('Corona Virus Visual')

text_style = dict(color='#444', fontFamily='sans-serif', fontWeight=300)

app.layout = html.Div([
    html.Div(
        html.H2('Corona Virus Time Series Data Visualization', style=text_style),
    ),
    html.Div(
        dcc.DatePickerSingle(
            id='date_picker',
            min_date_allowed=geo_master['date'].min(),
            max_date_allowed=geo_master['date'].max(),
            initial_visible_month=geo_master['date'].min(),
            date=geo_master['date'].min()
        )
    ),
    html.Div(id='corona_map_by_date'),
    html.Div([
        html.Div([
            html.Div(
                dcc.Dropdown(
                    id='loc_drop_down_1',
                    options=[{'label': i, 'value': i} for i in geo_master['Province/State'].unique()],
                    value='King County, WA'
                ),
                style={'width': '48%', 'display': 'inline-block'}
            ),
            html.Div(
                dcc.Dropdown(
                    id='loc_drop_down_2',
                    options=[{'label': i, 'value': i} for i in geo_master['Province/State'].unique()],
                    value='Hubei'
                ),
                style={'width': '48%', 'align': 'right', 'display': 'inline-block'}
            )
        ]),
        html.Div([
            html.Div(
                dcc.Graph(
                    id='loc_graph_1'
                ),
                style={'width': '48%', 'display': 'inline-block'}
            ),
            html.Div(
                dcc.Graph(
                    id='loc_graph_2'
                ),
                style={'width': '48%', 'align': 'right', 'display': 'inline-block'}
            )
        ])
    ])
])



@app.callback(
    Output(component_id='loc_graph_1', component_property='figure'),
    [Input(component_id='loc_drop_down_1', component_property='value')]
)
def update_loc_graph_1(value):
    geo_master_subset = geo_master[geo_master['Province/State'] == value]
    fig = go.Figure(
        data=go.Scatter(
            x=geo_master_subset['date'],
            y=geo_master_subset['Confirmed'],
            name='Confirmed Cases'
        )
    )
    fig.add_scatter(x=geo_master_subset['date'], y=geo_master_subset['Deaths'], name='Deaths')
    fig.add_scatter(x=geo_master_subset['date'], y=geo_master_subset['Recovered'], name='Recovered')
    fig.update_layout(
        title=value,
        xaxis_title="Date",
        yaxis_title="Number of People"
    )
    return fig


@app.callback(
    Output(component_id='loc_graph_2', component_property='figure'),
    [Input(component_id='loc_drop_down_2', component_property='value')]
)
def update_loc_graph_2(value):
    geo_master_subset = geo_master[geo_master['Province/State'] == value]
    fig = go.Figure(
        data=[go.Scatter(
            x=geo_master_subset['date'],
            y=geo_master_subset['Confirmed'],
            name='Confirmed Cases'
        )]
    )
    fig.add_scatter(x=geo_master_subset['date'], y=geo_master_subset['Deaths'], name='Deaths')
    fig.add_scatter(x=geo_master_subset['date'], y=geo_master_subset['Recovered'], name='Recovered')
    fig.update_layout(
        title=value,
        xaxis_title="Date",
        yaxis_title="Number of People"
    )
    return fig


@app.callback(
    Output(component_id='corona_map_by_date', component_property='children'),
    [Input(component_id='date_picker', component_property='date')]
)
def update_corona_map(date):
    geo_master_subset = geo_master[geo_master['date'] == date]
    fig = go.Figure(
        go.Scattergeo(
                     lon=geo_master_subset['Long'],
                     lat=geo_master_subset['Lat'],
                     mode='markers',
                     customdata=np.stack((geo_master_subset['Confirmed'], geo_master_subset['Deaths'], geo_master_subset['Recovered'], geo_master_subset['Province/State']), axis=-1),
                     marker=dict(
                         size=geo_master_subset['Confirmed_Size']*1.75,
                         color=geo_master_subset['Deaths_Color'],
                         colorscale=scl
                     ),
                     hovertemplate='<b>%{customdata[3]}</b><br><br>' + 
                                   '<b>Confirmed Cases</b>: %{customdata[0]}<br>' +
                                   '<b>Deaths</b>: %{customdata[1]}<br>' +
                                   '<b>Recovered</b>: %{customdata[2]}'
                     )
    )
    fig.update_geos(
        showcountries=True,
        projection_type='natural earth',
        landcolor='#cccccc',
        showocean=True,
        oceancolor='#a8d7ff'
    )
    fig.update_layout(height=300, margin={"r":0,"t":0,"l":0,"b":0})
    return dcc.Graph(id='corona_map', figure=fig)


app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})

app.server.run()