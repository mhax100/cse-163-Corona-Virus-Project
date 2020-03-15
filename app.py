"""
Maxwell Haak
Final Project
3/12/20
Program requests and stores data from a github repo, transforms and cleans data
for processing, calcultaes aggregate statistics, creates an animated map 
representing the spread of corona virus over time, and creates a dash app that
lets users interact with the map and line graph figures manually.
"""
# imports for dash app
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
# imports for data handling
import requests
import geopandas
import pandas as pd
import math
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime as dt


# Various methods used for data handling
def get_data(url, file_name):
    """
    Takes a url and file name to write to, and stores the
    requested data in the file name specified.
    """
    r = requests.get(url, allow_redirects=True)
    with open(file_name, 'wb') as f:
        f.write(r.content)


def pd_0(file_name):
    """
    Takes a file_name for a csv file and returns a pandas dataframe
    with any na values filled with 0.
    """
    frame = pd.read_csv(file_name)
    frame.fillna(0)
    return frame


def log_unless_zero(input):
    """
    Takes an integer input and returns the log of the integer, unless
    the input is 0, in which case it returns 0. Mainly used to convert
    data to the logarithmic scale for less extreme presentation in graphs.
    """
    if (input == 0):
        return 0
    else:
        return math.log(input)


def remove_us_counties(df):
    """
    Takes a dataframe as input and returns a modified version of the dataframe,
    where any loction that is both in the US and not a state is removed. This
    was implemented due to the discontinuation of data updates for counties in
    Johns Hopkins' Dataset.
    """
    states = ('Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
    'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois',
    'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland',
    'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana',
    'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
    'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania',
    'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah',
    'Vermont', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming',
    'District of Columbia', 'Diamond Princess', 'Grand Princess')
    not_state = (df['Province/State'].isin(states))
    is_us = df['Country/Region'] == 'US'
    is_not_us = df['Country/Region'] != 'US'
    return df[((not_state) & (is_us)) | (is_not_us)]


def melter(df, value_col, id_cols):
    """
    Takes a dataframe, column name to specify the name for the value column
    after the dataframe has been transformed, and list of column names to
    specify which columns should not be changed. Returns a dataframe with dates
    in one column and their corresponding values in another column.
    """
    recent_date = df.columns[-1]
    return df.melt(id_vars=id_cols,
                   value_vars=df.loc[:, '1/22/20':recent_date].columns,
                   var_name='date', value_name=value_col)


# Setting url's for the three csv files used.
url_confirmed = ('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/'
                 'master/csse_covid_19_data/csse_covid_19_time_series/'
                 'time_series_19-covid-Confirmed.csv')

url_deaths = ('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/'
              'master/csse_covid_19_data/csse_covid_19_time_series/'
              'time_series_19-covid-Deaths.csv')

url_recovered = ('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/'
                 'master/csse_covid_19_data/csse_covid_19_time_series/'
                 'time_series_19-covid-Recovered.csv')

# Writing the data into local csv files.
get_data(url_confirmed, 'covid19_confirmed.csv')
get_data(url_deaths, 'covid19_deaths.csv')
get_data(url_recovered, 'covid19_recovered.csv')

# Initializing geopandas dataframes from csv files.
confirmed = pd_0('covid19_confirmed.csv')
deaths = pd_0('covid19_deaths.csv')
recovered = pd_0('covid19_recovered.csv')

# Removing US Counties counts
confirmed = remove_us_counties(confirmed)
deaths = remove_us_counties(deaths)
recovered = remove_us_counties(recovered)

# Branching to country totals
confirmed_by_Country = confirmed.groupby(['Country/Region'], as_index=False).sum()
deaths_by_Country = deaths.groupby(['Country/Region'], as_index=False).sum()
recovered_by_Country = recovered.groupby(['Country/Region'], as_index=False).sum()

# Transforming geopandas dataframe from multiple to one date column.
confirmed = melter(confirmed, 'Confirmed', ['Province/State', 'Country/Region', 'Lat', 'Long'])
deaths = melter(deaths, 'Deaths', ['Province/State', 'Country/Region', 'Lat', 'Long'])
recovered = melter(recovered, 'Recovered', ['Province/State', 'Country/Region', 'Lat', 'Long'])

confirmed_by_Country = melter(confirmed_by_Country, 'Confirmed', ['Country/Region','Lat', 'Long'])
deaths_by_Country = melter(deaths_by_Country, 'Deaths', ['Country/Region','Lat', 'Long'])
recovered_by_Country = melter(recovered_by_Country, 'Recovered', ['Country/Region','Lat', 'Long'])


# Combining confirmed, deaths, and recovered data into one dataframe.
cols_to_use = deaths.columns.difference(confirmed.columns)
master = pd.merge(confirmed, deaths[cols_to_use],
                      left_index=True, right_index=True, how='outer')
cols_to_use = recovered.columns.difference(master.columns)
master = pd.merge(master, recovered[cols_to_use],
                      left_index=True, right_index=True, how='outer')

cols_to_use = deaths_by_Country.columns.difference(confirmed_by_Country.columns)
master_by_Country = pd.merge(confirmed_by_Country, deaths_by_Country[cols_to_use],
                      left_index=True, right_index=True, how='outer')
cols_to_use = recovered_by_Country.columns.difference(master_by_Country.columns)
master_by_Country = pd.merge(master_by_Country, recovered_by_Country[cols_to_use],
                      left_index=True, right_index=True, how='outer')

master.loc[master['Province/State'].isnull(), 'Province/State'] = master['Country/Region']

# Space for computing summary statistics from dataset
dates = master['date'].unique()
today = master[master['date'] == dates[-1]]

print(master)
grouped_date = master.groupby(['date'], as_index=False)
print(grouped_date['Confirmed'].sum())

most_confirmed_province = today.loc[today['Confirmed'].idxmax(),
                                        'Province/State']
most_deaths_province = today.loc[today['Deaths'].idxmax(),
                                     'Province/State']
most_recovered_province = today.loc[today['Recovered'].idxmax(),
                                        'Province/State']

today_by_Country = master_by_Country[master_by_Country['date'] == dates[-1]]
confirmed_id = today_by_Country['Confirmed'].idxmax()
most_confirmed_country = today_by_Country.loc[confirmed_id, 'Country/Region']
deaths_id = today_by_Country['Deaths'].idxmax()
most_deaths_country = today_by_Country.loc[deaths_id, 'Country/Region']
recovered_id = today_by_Country['Recovered'].idxmax()
most_recovered_country = today_by_Country.loc[recovered_id, 'Country/Region']

world_total_confirmed = today['Confirmed'].sum()
world_total_deaths = today['Deaths'].sum()
world_total_recovered = today['Recovered'].sum()

aggregate_val = {'Total Confirmed Cases': [world_total_confirmed],
                 'Total Deaths': [world_total_deaths],
                 'Total Recovered': [world_total_recovered]}
aggregate_val = pd.DataFrame(aggregate_val)
print(aggregate_val)


master['percent_deaths'] = master['Deaths'] / master['Confirmed']
master['percent_recovered'] = master['Recovered'] / master['Confirmed']
check = master[master['Province/State'] == 'Italy']
print(check)



# Creating columns for graphical display use.
master['Confirmed_Size'] = master.apply(lambda x: log_unless_zero(x['Confirmed']), axis=1)
master['Deaths_Color'] = master.apply(lambda x: log_unless_zero(x['Deaths']), axis=1)

# Converting dates in the dataframe to datetime objects
master['date_time'] = pd.to_datetime(master['date'], format='%m/%d/%y')

# Setting color scale for corona virus map.
scl = [[0, '#efedf5'], [1.0, '#756bb1']]
scl_anim = [[0, '#fee0d2'], [1.0, '#de2d26']]

# Create Figure with Corona Virus Map Animation
frames_list = []

# Adding frames to frameslist
for date in dates:
    master_subset = master[master['date_time'] == date]
    master_washington = master_subset[master_subset['Province/State'] == 'Washington']
    frames_list.append(go.Frame(data=[go.Scattergeo(
                     lon=master_subset['Long'],
                     lat=master_subset['Lat'],
                     mode='markers',
                     customdata=np.stack((master_subset['Confirmed'],
                                          master_subset['Deaths'],
                                          master_subset['Recovered'],
                                          master_subset['Province/State']),
                                          axis=-1),
                     marker=dict(
                         size=master_subset['Confirmed_Size']*1.75,
                         color=master_subset['Deaths_Color'],
                         colorscale=scl_anim
                     ),
                     hovertemplate='<b>%{customdata[3]}</b><br><br>' +
                                   '<b>Confirmed Cases</b>: %{customdata[0]}<br>' +
                                   '<b>Deaths</b>: %{customdata[1]}<br>' +
                                   '<b>Recovered</b>: %{customdata[2]}'
                     )],
                     layout=go.Layout(
                         title='Date: ' + str(master_washington['date'])
                     )
                     ))

# Constructing animation with frameslist
fig_anim = go.Figure(
    data=[go.Scattergeo(
                     lon=master['Long'],
                     lat=master['Lat'],
                     mode='markers',
                     customdata=np.stack((master['Confirmed'], master['Deaths'], master['Recovered'], master['Province/State']), axis=-1),
                     marker=dict(
                         size=master['Confirmed_Size']*1.75,
                         color=master['Deaths_Color'],
                         colorscale=scl_anim,
                         colorbar_title='Deaths (Natural Log Scale)'
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

# Showing animation
fig_anim.show()

# Initializing dash app
app = dash.Dash(__name__)

server = app.server

text_style = dict(color='#444', fontFamily='sans-serif', fontWeight=300)

# App Layout
app.layout = html.Div(
    children=[
        html.Div(
            html.H1('Corona Virus Time Series Data Visualization',
                    style=text_style)
        ),
        html.Div(
            html.H2('DISCLAIMER', style=text_style)
        ),
        html.Div(
            html.P('''The data for this visualization is from the Center for
                   Systems Science and Engingeering at Johns Hopkins University
                   , and has many limitations. This visualization is in no way
                   affiliated with or represents Johns Hopkins University. As
                   information on Corona Virus and COVID-19 is constantly
                   changing, the data presented here is likely to change and be
                   updated more accurately as the state of available
                   information evolves. In addition, the dataset only measures
                   the number of Confirmed Cases (cases where the person has
                   been officially confirmed via laboratory testing to be
                   infected by COVID-19) and most likely does not represent
                   the total number of cases worldwide. This could be because
                   people who only present mild symptoms may never be tested
                   and even when severe symptoms are presented not every
                   country is equipped to test every person. Regardless of the
                   reason, the number of total cases is most likely larger than
                   the number of confirmed cases because not everyone that
                   has been infected is necessarily tested.''',
                   style=text_style)
        ),
        html.Div([
            html.P('''Furthermore, the visualizations here are by no means
                   comprehensive and I encourage everyone to look at other
                   sources to learn more about COVID-19. Should the dataset
                   which these visualizations use change sifnificantly, the
                   data presented could become innacurate or out of date. As
                   such, I encourage people to double check the information
                   at any of these links:
                   - The Dataset these visualizations use:
                   https://github.com/CSSEGISandData/2019-nCoV
                   - Visualization by Johns Hopkins: 
                   - The ourworldindata page for Corona Virus:
                   To the best of my knowledge all of these links are safe to
                   follow.''',
                   style=text_style),
            html.P('Test', style=text_style)
        ]),
        html.Div([
            html.Div(
                dcc.DatePickerSingle(
                    id='date_picker',
                    min_date_allowed=master['date_time'].min(),
                    max_date_allowed=master['date_time'].max(),
                    initial_visible_month=master['date_time'].min(),
                    date=master['date_time'].min(),
                    style={'border': '1px solid black'}
                )
            ),
            html.Div([
                html.Div(
                    dcc.Graph(id='corona_map'),
                    style={'width': '70%', 'display': 'inline-block'}
                ),
                html.Div(
                    dash_table.DataTable(
                        id='ag_table',
                        columns=[{"name": i, "id": i} for i in aggregate_val.columns],
                        data=aggregate_val.to_dict('records'),
                    ),
                    style={'width': '18%', 'align': 'right', 'display': 'inline-block'}
                )
            ])
        ]),
        html.Div([
            html.Div([
                html.Div(
                    dcc.Dropdown(
                        id='loc_drop_down_1',
                        options=[{'label': i, 'value': i} for i in master['Province/State'].unique()],
                        value='Washington'
                    ),
                    style={'width': '48%', 'display': 'inline-block'}
                ),
                html.Div(
                    dcc.Dropdown(
                        id='loc_drop_down_2',
                        options=[{'label': i, 'value': i} for i in master['Province/State'].unique()],
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
        ]),
        html.Div([
            html.Div([
                html.Div(
                    dcc.Dropdown(
                        id='loc_perc_drop_down_1',
                        options=[{'label': i, 'value': i} for i in master['Province/State'].unique()],
                        value='Washington'
                    ),
                    style={'width': '48%', 'display': 'inline-block'}
                ),
                html.Div(
                    dcc.Dropdown(
                        id='loc_perc_drop_down_2',
                        options=[{'label': i, 'value': i} for i in master['Province/State'].unique()],
                        value='Hubei'
                    ),
                    style={'width': '48%', 'align': 'right', 'display': 'inline-block'}
                )
            ]),
            html.Div([
                html.Div(
                    dcc.Graph(
                        id='loc_perc_graph_1'
                    ),
                    style={'width': '48%', 'display': 'inline-block'}
                ),
                html.Div(
                    dcc.Graph(
                        id='loc_perc_graph_2'
                    ),
                    style={'width': '48%', 'align': 'right', 'display': 'inline-block'}
                )
            ])
        ])
    ]
)


@app.callback(
    Output(component_id='loc_graph_1', component_property='figure'),
    [Input(component_id='loc_drop_down_1', component_property='value')]
)
def update_loc_graph_1(value):
    """
    Return line graph for specified location on app callback.
    """
    master_subset = master[master['Province/State'] == value]
    fig = go.Figure(
        data=go.Scatter(
            x=master_subset['date_time'],
            y=master_subset['Confirmed'],
            name='Confirmed Cases'
        )
    )
    fig.add_scatter(x=master_subset['date_time'], y=master_subset['Deaths'], name='Deaths')
    fig.add_scatter(x=master_subset['date_time'], y=master_subset['Recovered'], name='Recovered')
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
    """
    Return line graph for specified location on app callback.
    """
    master_subset = master[master['Province/State'] == value]
    fig = go.Figure(
        data=[go.Scatter(
            x=master_subset['date_time'],
            y=master_subset['Confirmed'],
            name='Confirmed Cases'
        )]
    )
    fig.add_scatter(x=master_subset['date_time'], y=master_subset['Deaths'], name='Deaths')
    fig.add_scatter(x=master_subset['date_time'], y=master_subset['Recovered'], name='Recovered')
    fig.update_layout(
        title=value,
        xaxis_title="Date",
        yaxis_title="Number of People"
    )
    return fig

@app.callback(
    Output(component_id='loc_perc_graph_1', component_property='figure'),
    [Input(component_id='loc_perc_drop_down_1', component_property='value')]
)
def update_loc_perc_graph_1(value):
    """
    Return percentage line graph for specified location on app callback.
    """
    master_subset = master[master['Province/State'] == value]
    master_subset['pct_change_conf'] = master_subset.loc[:,'Confirmed'].pct_change()
    master_subset['pct_change_death'] = master_subset.loc[:,'Deaths'].pct_change()
    master_subset['pct_change_recov'] = master_subset.loc[:,'Recovered'].pct_change()
    fig = go.Figure(
        data=go.Scatter(
            x=master_subset['date_time'],
            y=master_subset['pct_change_conf'],
            name='Percent Change Confirmed'
        )
    )
    fig.add_scatter(x=master_subset['date_time'], y=master_subset['pct_change_death'], name='Percent Change Deaths')
    fig.add_scatter(x=master_subset['date_time'], y=master_subset['pct_change_recov'], name='Percent Change Recovered')
    fig.update_layout(
        title='Percentage Change for ' + value,
        xaxis_title="Date",
        yaxis_title="Number of People"
    )
    return fig


@app.callback(
    Output(component_id='loc_perc_graph_2', component_property='figure'),
    [Input(component_id='loc_perc_drop_down_2', component_property='value')]
)
def update_loc_perc_graph_2(value):
    """
    Return percentage line graph for specified location on app callback.
    """
    master_subset = master[master['Province/State'] == value]

    master_subset['pct_change_conf'] = master_subset.loc[:,'Confirmed'].pct_change()
    master_subset['pct_change_death'] = master_subset.loc[:,'Deaths'].pct_change()
    master_subset['pct_change_recov'] = master_subset.loc[:,'Recovered'].pct_change()

    fig = go.Figure(
        data=go.Scatter(
            x=master_subset['date_time'],
            y=master_subset['pct_change_conf'],
            name='Percent Change Confirmed'
        )
    )
    fig.add_scatter(x=master_subset['date_time'], y=master_subset['pct_change_death'], name='Percent Change Deaths')
    fig.add_scatter(x=master_subset['date_time'], y=master_subset['pct_change_recov'], name='Percent Change Recovered')
    fig.update_layout(
        title='Percentage Change for ' + value,
        xaxis_title="Date",
        yaxis_title="Number of People"
    )
    return fig


@app.callback(
    Output(component_id='corona_map', component_property='figure'),
    [Input(component_id='date_picker', component_property='date')]
)
def update_corona_map(date):
    """
    Return geo scatterplot map for specified date on app callback.
    """
    master_subset = master[master['date_time'] == date]
    fig = go.Figure(
        go.Scattergeo(
                     lon=master_subset['Long'],
                     lat=master_subset['Lat'],
                     mode='markers',
                     customdata=np.stack((master_subset['Confirmed'], master_subset['Deaths'], master_subset['Recovered'], master_subset['Province/State']), axis=-1),
                     marker=dict(
                         size=master_subset['Confirmed_Size']*1.75,
                         color=master_subset['Deaths_Color'],
                         colorscale=scl,
                         colorbar_title='Deaths (Natural Log Scale)'
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
    return fig


# CSS stylesheet
app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})


if __name__ == '__main__':
    app.run_server()

