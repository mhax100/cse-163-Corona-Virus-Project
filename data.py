# imports for data handling
import requests
import pandas as pd
import math


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


def log_unless_0(input):
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
    states = ('Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California',
              'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia',
              'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas',
              'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts',
              'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana',
              'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey',
              'New Mexico', 'New York', 'North Carolina', 'North Dakota',
              'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island',
              'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah',
              'Vermont', 'Virginia', 'Washington', 'West Virginia',
              'Wisconsin', 'Wyoming', 'District of Columbia',
              'Diamond Princess', 'Grand Princess')
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
confirmed_by_Country = confirmed.groupby(['Country/Region'],
                                         as_index=False).sum()
deaths_by_Country = deaths.groupby(['Country/Region'],
                                   as_index=False).sum()
recovered_by_Country = recovered.groupby(['Country/Region'],
                                         as_index=False).sum()

# Transforming geopandas dataframe from multiple to one date column.
confirmed = melter(confirmed, 'Confirmed', ['Province/State', 'Country/Region',
                                            'Lat', 'Long'])
deaths = melter(deaths, 'Deaths', ['Province/State', 'Country/Region', 'Lat',
                                   'Long'])
recovered = melter(recovered, 'Recovered', ['Province/State', 'Country/Region',
                                            'Lat', 'Long'])

confirmed_by_Country = melter(confirmed_by_Country,
                              'Confirmed', ['Country/Region', 'Lat', 'Long'])
deaths_by_Country = melter(deaths_by_Country,
                           'Deaths', ['Country/Region', 'Lat', 'Long'])
recovered_by_Country = melter(recovered_by_Country,
                              'Recovered', ['Country/Region', 'Lat', 'Long'])


# Combining confirmed, deaths, and recovered data into one dataframe.
cols_to_use = deaths.columns.difference(confirmed.columns)
master = pd.merge(confirmed, deaths[cols_to_use],
                  left_index=True, right_index=True, how='outer')
cols_to_use = recovered.columns.difference(master.columns)
master = pd.merge(master, recovered[cols_to_use],
                  left_index=True, right_index=True, how='outer')

conf_columns = confirmed_by_Country.columns
cols_to_use = deaths_by_Country.columns.difference(conf_columns)
master_by_Country = pd.merge(confirmed_by_Country,
                             deaths_by_Country[cols_to_use],
                             left_index=True, right_index=True, how='outer')
master_columns = master_by_Country.columns
cols_to_use = recovered_by_Country.columns.difference(master_columns)
master_by_Country = pd.merge(master_by_Country,
                             recovered_by_Country[cols_to_use],
                             left_index=True, right_index=True, how='outer')

master.loc[master['Province/State'].isnull(),
           'Province/State'] = master['Country/Region']

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
master['Confirmed_Size'] = master.apply(lambda x: log_unless_0(x['Confirmed']),
                                        axis=1)
master['Deaths_Color'] = master.apply(lambda x: log_unless_0(x['Deaths']),
                                      axis=1)

# Converting dates in the dataframe to datetime objects
master['date_time'] = pd.to_datetime(master['date'], format='%m/%d/%y')
