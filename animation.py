import dates
import master
import numpy as np
import plotly.graph_objects as go

# Set color scale for animation
scl_anim = [[0, '#fee0d2'], [1.0, '#de2d26']]

# Create Figure with Corona Virus Map Animation
frames_list = []

# Adding frames to frameslist
for date in dates:
    master_subset = master[master['date_time'] == date]
    is_washington = master_subset['Province/State'] == 'Washington'
    master_washington = master_subset[is_washington]
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
                                   '<b>Confirmed Cases</b>: %{customdata[0]}\
                                   <br>' +
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
                     customdata=np.stack((master['Confirmed'],
                                          master['Deaths'],
                                          master['Recovered'],
                                          master['Province/State']), axis=-1),
                     marker=dict(
                         size=master['Confirmed_Size']*1.75,
                         color=master['Deaths_Color'],
                         colorscale=scl_anim,
                         colorbar_title='Deaths (Natural Log Scale)'
                     ),
                     hovertemplate='<b>%{customdata[3]}</b><br><br>' +
                                   '<b>Confirmed Cases</b>: %{customdata[0]}\
                                    <br>' +
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
