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
import plotly.graph_objects as go
import master from data.py


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

