"""
Maxwell Haak
Final Project
3/12/20
Creates a dash app that lets users interact with the map and line graph
figures manually.
"""
# imports for dash app
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import numpy as np
from data import master
from data import today


# Setting color scale for corona virus map.
scl = [[0, '#efedf5'], [1.0, '#756bb1']]

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
                   , and has many limitations. Do not use the information presented here as a 
                   replacement for information from more legitimate sources such as the 
                   WHO or Johns Hopkins. This visualization is in no way
                   affiliated with or represents Johns Hopkins University. The data set
                   used in this project is no longer maintained by Johns Hopkins and is now
                   deprecated. For current statistics please visit Johns Hopkins' own dashboard.
                   ''',
                   style=text_style)
        ),
        html.Div([
            html.P('''This was mainly developed as a class project with the intent
                    of developing my skills with python, so data may be innacurate.
                   ''',
                   style=text_style)
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
                    style={'width': '74%', 'display': 'inline-block'}
                ),
                html.Div([
                    dcc.Dropdown(
                            id='loc_drop_down_3',
                            options=[{'label': i, 'value': i} for i in
                                     today['Province/State'].unique()],
                            value='Total'
                    ),
                    html.Div([
                        html.Div(
                            html.H1(id='Confirmed'), style={'height': '25%'}
                        ),
                        html.Div(
                            html.H1(id='Deaths'), style={'height': '25%'}
                        ),
                        html.Div(
                            html.H1(id='Recovered'), style={'height': '25%'}
                        )
                    ])
                ], style={'width': '25%', 'display': 'inline-block', 'vertical-align': 'top'}
                )
            ])
        ]),
        html.Div([
            html.Div([
                html.Div(
                    dcc.Dropdown(
                        id='loc_drop_down_1',
                        options=[{'label': i, 'value': i} for i in
                                 master['Province/State'].unique()],
                        value='Italy'
                    ),
                    style={'width': '48%',
                           'display': 'inline-block'}
                ),
                html.Div(
                    dcc.Dropdown(
                        id='loc_drop_down_2',
                        options=[{'label': i, 'value': i} for i in
                                 master['Province/State'].unique()],
                        value='Hubei'
                    ),
                    style={'width': '48%',
                           'align': 'right',
                           'display': 'inline-block'}
                )
            ]),
            html.Div([
                html.Div(
                    dcc.Graph(
                        id='loc_graph_1'
                    ),
                    style={'width': '48%',
                           'display': 'inline-block'}
                ),
                html.Div(
                    dcc.Graph(
                        id='loc_graph_2'
                    ),
                    style={'width': '48%',
                           'align': 'right',
                           'display': 'inline-block'}
                )
            ])
        ])
    ]
)


@app.callback(
    [Output(component_id='Confirmed', component_property='children'),
     Output(component_id='Deaths', component_property='children'),
     Output(component_id='Recovered', component_property='children')],
    [Input(component_id='loc_drop_down_3', component_property='value')]
)
def update_confirmed_text(location):
    today_subset = today[today['Province/State'] == location]
    confirmed = int(today_subset['Confirmed'])
    deaths = int(today_subset['Deaths'])
    recovered = int(today_subset['Recovered'])
    confirmed_str = 'Confirmed: ' + str(confirmed)
    deaths_str = 'Deaths: ' + str(deaths)
    recovered_str = 'Recovered: ' + str(recovered)
    return confirmed_str, deaths_str, recovered_str


@app.callback(
    Output(component_id='loc_graph_1', component_property='figure'),
    [Input(component_id='loc_drop_down_1', component_property='value')]
)
def update_loc_graph_1(location):
    """
    Return line graph for specified location on app callback.
    """
    master_subset = master[master['Province/State'] == location]
    fig = go.Figure(
        data=go.Scatter(
            x=master_subset['date_time'],
            y=master_subset['Confirmed'],
            name='Confirmed Cases'
        )
    )
    fig.add_scatter(x=master_subset['date_time'], y=master_subset['Deaths'],
                    name='Deaths')
    fig.add_scatter(x=master_subset['date_time'], y=master_subset['Recovered'],
                    name='Recovered')
    fig.update_layout(
        title=location,
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
    fig.add_scatter(x=master_subset['date_time'], y=master_subset['Deaths'],
                    name='Deaths')
    fig.add_scatter(x=master_subset['date_time'], y=master_subset['Recovered'],
                    name='Recovered')
    fig.update_layout(
        title=value,
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
                     customdata=np.stack((master_subset['Confirmed'],
                                          master_subset['Deaths'],
                                          master_subset['Recovered'],
                                          master_subset['Province/State']),
                                         axis=-1),
                     marker=dict(
                         size=master_subset['Confirmed_Size']*1.75,
                         color=master_subset['Deaths_Color'],
                         colorscale=scl,
                         colorbar_title='Deaths (Natural Log Scale)'
                     ),
                     hovertemplate='<b>%{customdata[3]}</b><br><br>' +
                                   '<b>Confirmed Cases</b>: %{customdata[0]}\
                                    <br>' +
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
    fig.update_layout(height=300, margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig


# CSS stylesheet
app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})


app.server.run()
