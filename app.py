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


def distance_hubei(lat, long):
    lat_hubei = geo_confirmed[geo_confirmed['Province/State'] == 'Hubei']['Lat']
    long_hubei = geo_confirmed[geo_confirmed['Province/State'] == 'Hubei']['Long']
    lat_dest = lat
    long_dest = long
    radius = 6371 # km
    dlat = math.radians(lat_dest-lat_hubei)
    dlon = math.radians(long_dest-long_hubei)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat_hubei)) \
        * math.cos(math.radians(lat_dest)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c
    return d


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


"""
At a later date reimplement Distance to Hubei column. Was working
but now getting cannot convert series to float error. Besides uncommenting
this code chunk, also need to add 'Distance_Hubei(km)' back to the columns
being marked as id columns in geo_melter().
"""
#geo_confirmed['Distance_Hubei_(km)'] = geo_confirmed.apply(lambda x: distance_hubei(x['Lat'], x['Long']), axis=1)
#geo_deaths['Distance_Hubei_(km)'] = geo_deaths.apply(lambda x: distance_hubei(x['Lat'], x['Long']), axis=1)
#geo_recovered['Distance_Hubei_(km)'] = geo_recovered.apply(lambda x: distance_hubei(x['Lat'], x['Long']), axis=1)

geo_confirmed_melted = geo_melter(geo_confirmed, 'Confirmed')
geo_deaths_melted = geo_melter(geo_deaths, 'Deaths')
geo_recovered_melted = geo_melter(geo_recovered, 'Recovered')

cols_to_use = geo_deaths_melted.columns.difference(geo_confirmed_melted.columns)
geo_master = pd.merge(geo_confirmed_melted, geo_deaths_melted[cols_to_use], left_index=True, right_index=True, how='outer')
cols_to_use = geo_recovered_melted.columns.difference(geo_master.columns)
geo_master = pd.merge(geo_master, geo_recovered_melted[cols_to_use], left_index=True, right_index=True, how='outer')

geo_master['Confirmed_Size'] = geo_master.apply(lambda x: log_unless_zero(x['Confirmed']), axis=1)
geo_master.head()
geo_master['text'] = (', Confirmed: ' + geo_master['Confirmed'].astype(str)
                      + ', Deaths: ' + geo_master['Deaths'].astype(str)
                      + ', Recovered: ' + geo_master['Recovered'].astype(str))

geo_master['date'] = pd.to_datetime(geo_master['date'], format='%m/%d/%y')



"""
Make an interactive table that returns number of people confirmed, dead, recovered in the date range specified
and the location specified. Drop downs for location and text input for date. 
"""


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
    html.Div(id='corona_map_by_date')
])

@app.callback(
    Output(component_id='corona_map_by_date', component_property='children'),
    [Input(component_id='date_picker', component_property='date')]
)
def update_corona_map(date):
    geo_master_subset = geo_master[geo_master['date'] == date]
    return dcc.Graph(id='corona_map', figure=px.scatter_geo(geo_master_subset, lat='Lat', lon='Long', size='Confirmed_Size', color='Deaths', hover_name='Province/State', text='text'))

app.server.run()