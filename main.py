import requests
import geopandas
import pandas as pd
import matplotlib.pyplot as plt
import math
import numpy as np


def get_data(url, file_name):
    r = requests.get(url, allow_redirects=True)
    with open(file_name, 'wb') as f:
        f.write(r.content)


def geo_convert(file_name):
    frame = pd.read_csv(file_name)
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
geo_recovered = geo_convert('covid19_deaths.csv')

countries = geopandas.read_file('Countries_WGS84.shp')

hubei_lat = geo_confirmed[geo_confirmed['Province/State'] == 'Hubei']['Lat']
hubei_long = geo_confirmed[geo_confirmed['Province/State'] == 'Hubei']['Long']

geo_confirmed['Lat_Delta_Hubei'] = np.radians(
    geo_confirmed['Lat'].astype(float)) - math.radians(hubei_lat)
geo_confirmed['Long_Delta_Hubei'] = np.radians(
    geo_confirmed['Long'].astype(float)) - math.radians(hubei_long)
geo_confirmed['Distance_Hubei'] = geo_confirmed.apply(lambda x: distance_hubei(x['Lat'], x['Long']), axis=1)

print(geo_confirmed)
