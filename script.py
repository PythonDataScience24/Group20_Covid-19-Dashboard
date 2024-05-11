import pandas as pd
import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import plotly.express as px

# Define global variables
df = None
app = dash.Dash(__name__)

# Constants
data_path = './data/WHO-COVID-19-global-data.csv'
region_data_path = './data/region.csv'
population_data_path = './data/populations.csv'
population_normalizer = 1000000


def import_data():
    # Import the covid 19 data from WHO-COVID-19-global-data.csv
    df = pd.read_csv(data_path)

    # We need the 3-letter code to join with the population data
    # Get 3-letter country code from 'regions.csv', data from a previous exercise.
    regions = pd.read_csv(region_data_path)

    # Get population per country from a manual CSV export from the World Bank:
    # https://databank.worldbank.org/source/population-estimates-and-projections#
    # For simplicity, use a static population number: the average population between 2019 and 2021
    population = pd.read_csv(population_data_path)

    return df, regions, population


def preprocess_data(df, regions, population):
    df['Date_reported'] = pd.to_datetime(df['Date_reported'])
    df = pd.merge(df, regions[['alpha-2', 'alpha-3']], left_on='Country_code', right_on='alpha-2')
    population['population'] = np.divide(
        (population['2019 [YR2019]'] + population['2020 [YR2020]'] + population['2021 [YR2021]']), 3.0)
    df = pd.merge(df, population[['Country Code', 'population']], left_on='alpha-3', right_on='Country Code')
    # Replace missing values by 0
    df = df.fillna(0)
    # Drop unnecessary columns
    df = df.drop(columns=['alpha-2', 'alpha-3', 'Country Code'])
    

    return df


def calculate_rt(df):
    """
    Calculate Rt numbers for each country.

    Parameter:
        df (DataFrame): df containing Covid19 data

    Returns :
        df (DataFrame): df with calculated rt number
    """
    # Use the approximation: Rt = n(t) / n(t-1), where n(t) is new infected at time t. The approximation is from:
    # https://medium.com/@m.pierini/time-varying-reproduction-number-rt-theory-and-python-implementation-part-i-basics-and-epiestim-99ea5fc30f51
    df['Rt'] = df['New_cases'] / df['New_cases'].shift(1)

    # Fill rt for new occurrences with number rt number of next day (possible changing approach later)
    df.loc[df['Rt'] == np.inf, 'Rt'] = df['Rt'].shift(-1)  # different approach df['New_cases'] to be determined later

    if df['New_cases'].iloc[0] != 0:
        df['Rt'].iloc[0] = df['Rt'].iloc[1]

    # Fill rest with 0
    df['Rt'] = df['Rt'].fillna(0)

    return df


def calculate_deaths_per_cases(df):
    df['deaths_per_cases'] = df['Cumulative_deaths'] / df['Cumulative_cases']
    df['deaths_per_cases'] = df['deaths_per_cases'].fillna(0)
    return df


def calc_stats(df, for_whom):
    """
    Calculate stats related to COVID-19 cases and deaths.

    Parameters:
        df (DataFrame): df containing COVID-19 data.
        for_whom (str): column to group the data for calculation

    Returns:
        df (DataFrame): original df with calculated stats
        df_norm (DataFrame): df with normalized data for stats 3 and 5.
    """
    # Compute deaths per cases (stat 1)
    df = calculate_deaths_per_cases(df)

    # Number of cases (stat 2) is the column 'New_cases' and number of deaths (stat 4) is the column 'New_deaths'

    # Compute rt number (stat 6)
    df['Rt'] = 0
    df = df.groupby(for_whom, group_keys=True).apply(calculate_rt)

    # Create a new dataframe for normalized data for stats 3 and 5
    df_norm = normalize(df)
    return df, df_norm


def normalize(df):
    """
    Normalizes the data according to population size and scales it up to cases or deaths per 1000000 inhabitants.
    Important for statistics 3 and 5.

    Parameter:
        df (Dataframe): df containing Covid19 data

    Returns:
        df_norm (Dataframe): df with normalized Case numbers and deaths per 1000000
    """
    df_norm = df.copy()
    cols_normalize = ['New_cases', 'Cumulative_cases', 'New_deaths', 'Cumulative_deaths']

    df_norm[cols_normalize] = df_norm[cols_normalize].div(df_norm['population'], axis=0) * population_normalizer

    return df_norm

def generate_line_plot(df, selected_countries, data_col):
        """
        Creates a line graph illustrating the development of a specified data column 
        (e.g. Cases, Deaths) over a period of time.

        Parameters:
        - df (dataframe) : dataframe containing values within date range
        - selected_countries (list): list of countries for which the user selected
        - data_col (str): name of the column for which values the line graph will be plotted

        Returns:
        - fig (plotly.graph_objects.Figure): line graph showing development of value in specified column
        """

        # Creates a figure
        fig = go.Figure()
        # Changes the name for the graph title and axis title
        name_of_graph = data_col.replace('_', ' ').replace('New ', '').capitalize()
        

        # Adds for every selected country a line graph over the given time period
        for country in selected_countries:
            selected_country_data  = df[df['level_0'] == country]
            fig.add_trace(go.Scatter(x=selected_country_data['Date_reported'], y=selected_country_data[data_col], mode='lines', name=country))

        # Sets the title and the axis titles of the graph
        fig.update_layout(title=f'{name_of_graph} by Country', yaxis_title=f'# of {name_of_graph}')
        return fig

def append_dataframes(df, df_regions):
    """
    Appends two dataframes containing data for country and regions together by reindexing the columns of the first dataframe.

        Parameters:
        - df (dataframe) : dataframe containing Covid data for the countries
        - df_regions (dataframe) : dataframe containing Covid data for the regions

        Returns:
        - df (dataframe) : dataframe containing Covid data for the countries and regions
    """
    # Appending the two dataframes together
    df = df.set_index(['Country', 'Date_reported'])
    df_regions = df_regions.reset_index(level=[1])
    df = df._append(df_regions)

    # Flattens the dataframe
    df = df.reset_index()
    return df

def main():
    global df  # Define df as global variable
    # Import the data
    df, regions, population = import_data()

    # Preprocess data
    df = preprocess_data(df, regions, population)

    # Compute stats for countries
    df, df_norm = calc_stats(df, 'Country')

    # Compute stats for regions in separate dataframes
    columns_to_sum = ['New_cases', 'Cumulative_cases', 'New_deaths', 'Cumulative_deaths', 'population']

    df_regions = df.groupby(['WHO_region', 'Date_reported'])[columns_to_sum].sum()
    df_regions, df_regions_norm = calc_stats(df_regions, 'WHO_region')

    # Append dataframes together
    df = append_dataframes(df, df_regions)


    # Initialize Dash app
    app.layout = html.Div([
        html.H1('Covid-19'),
        html.Div(
        [   html.Label('Select Country'),
            dcc.Dropdown(
            id='country-dropdown',
            options=[{'label': country, 'value': country} for country in df['level_0'].unique()],
            value=['Switzerland'],  # Default value
            multi=True
        ),
            html.Label('Select timeframe: '),
            dcc.DatePickerRange(
                id='date-picker',
                start_date=df['Date_reported'].min(),
                end_date=df['Date_reported'].max(),
                display_format='MM/YYYY',)
                

        ], id='control-container', style={'display': 'flex', 'flex-direction': 'row'}),
        
        html.Div([
            dcc.Graph(id='cases-graph'),
            dcc.Graph(id='deaths-graph'),
        ], style={'display': 'flex', 'flex-direction': 'row'}),
    ])


    @app.callback(
        [Output('cases-graph', 'figure'),
         Output('deaths-graph', 'figure')],
        [Input('country-dropdown', 'value'),
         Input('date-picker', 'start_date'),
         Input('date-picker', 'end_date')]
    )
    def update_graphs(selected_countries, start_date, end_date):
        # filter so only within given time range cases and deaths computed 
        df_filtered = df[(df['Date_reported'] >= start_date) & (df['Date_reported'] <= end_date)]

        # graph showing number of cases over selected time period
        fig_cases = generate_line_plot(df_filtered, selected_countries, "New_cases")

        # graph showing number of deaths over selected time period
        fig_deaths = generate_line_plot(df_filtered, selected_countries, "New_deaths")

        return fig_cases, fig_deaths

    # Run the app
    app.run_server(debug=True)


# Call main function
if __name__ == '__main__':
    main()
