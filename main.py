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
print(geo_confirmed_melted.loc[2176])
print(geo_deaths_melted.loc[2176])
print(geo_recovered_melted.loc[2176])

cols_to_use = geo_deaths_melted.columns.difference(geo_confirmed_melted.columns)
geo_master = pd.merge(geo_confirmed_melted, geo_deaths_melted[cols_to_use], left_index=True, right_index=True, how='outer')
cols_to_use = geo_recovered_melted.columns.difference(geo_master.columns)
geo_master = pd.merge(geo_master, geo_recovered_melted[cols_to_use], left_index=True, right_index=True, how='outer')
print(geo_master.loc[176, 'Deaths'])
print(geo_master.loc[0])

geo_master['Confirmed_Size'] = geo_master.apply(lambda x: log_unless_zero(x['Confirmed']), axis=1)
geo_master.head()
geo_master['text'] = ('(' + geo_master['Lat'].astype(str) + ', ' +
                        geo_master['Long'].astype(str) + ')' + ', Confirmed: '
                        + geo_master['Confirmed'].astype(str) + ', Deaths: '
                        + geo_master['Deaths'].astype(str) + ', Recovered: '
                        + geo_master['Recovered'].astype(str))

geo_master['date'] = pd.to_datetime(geo_master['date'], format='%m/%d/%y')

dates = geo_master.date.unique()



"""
Make an interactive table that returns number of people confirmed, dead, recovered in the date range specified
and the location specified. Drop downs for location and text input for date. 
"""

"""
Dead Code to work on implementing at a later date.
"""

"""
At a later date reimplement Distance to Hubei column. Was working
but now getting cannot convert series to float error. Besides uncommenting
this code chunk, also need to add 'Distance_Hubei(km)' back to the columns
being marked as id columns in geo_melter().

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

geo_confirmed['Distance_Hubei_(km)'] = geo_confirmed.apply(lambda x: distance_hubei(x['Lat'], x['Long']), axis=1)
geo_deaths['Distance_Hubei_(km)'] = geo_deaths.apply(lambda x: distance_hubei(x['Lat'], x['Long']), axis=1)
geo_recovered['Distance_Hubei_(km)'] = geo_recovered.apply(lambda x: distance_hubei(x['Lat'], x['Long']), axis=1)
"""

"""
Animation of the corona virus map. Works in just plotly, but having trouble integrating into the dashboard.

dates = geo_master['date'].unique()
frames_list = []
for date in dates:
    geo_master_subset = geo_master[geo_master['date'] == date]
    frames_list.append(go.Frame(data=[go.Scattergeo(
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
                     )]))

fig_anim = go.Figure(
    data=[go.Scattergeo(
                     lon=geo_master['Long'],
                     lat=geo_master['Lat'],
                     mode='markers',
                     customdata=np.stack((geo_master['Confirmed'], geo_master['Deaths'], geo_master['Recovered'], geo_master['Province/State']), axis=-1),
                     marker=dict(
                         size=geo_master['Confirmed_Size']*1.75,
                         color=geo_master['Deaths_Color'],
                         colorscale=scl
                     ),
                     hovertemplate='<b>%{customdata[3]}</b><br><br>' + 
                                   '<b>Confirmed Cases</b>: %{customdata[0]}<br>' +
                                   '<b>Deaths</b>: %{customdata[1]}<br>' +
                                   '<b>Recovered</b>: %{customdata[2]}'
                     )],
    layout=go.Layout(
        updatemenus=[dict(type="buttons",
                          buttons=[dict(label="Play",
                                        method="animate",
                                        args=[None])])]),
    frames=frames_list
    )
"""

"""
        dcc.Dropdown(
            id='type_drop_down',
            options=[
                {'label': 'Line Graph', 'value'='line'},
                {'label': 'Bar Chart', 'value'='bar'}
            ],
            value='line'
        ),
        ,
        ,
        dcc.Graph(
            id='loc_graph_2'
        )

@app.callback(
    Output(component_id='loc_graph_1', component_property='figure'),
    [Input(component_id='loc_drop_down_1', component_property='value')]
)
def update_loc_graph_1(value):
    geo_master_subset = geo_master[geo_master['Province/State'] == value]
    fig = go.Figure(
        data=go.Scatter(
            x=geo_master_subset['date'],
            y=geo_master_subset['Confirmed']
        )
    )
    return fig


@app.callback(
    Output(component_id='loc_graph_2', component_property='figure'),
    [Input(component_id='loc_drop_down_2', component_property='value')]
)
def update_loc_graph_2(value):
    geo_master_subset = geo_master[geo_master['Province/State'] == value]
    fig = go.Figure(
        data=go.Scatter(
            x=geo_master_subset['date'],
            y=geo_master_subset['Confirmed']
        )
    )
    return fig
"""