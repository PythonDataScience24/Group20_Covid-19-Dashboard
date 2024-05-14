"""
This module contains a dashboard application for visualizing COVID-19 data.
It includes data processing, normalization, and visualization using Dash.
"""
import pandas as pd
import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

# Constants
DATA_PATH = './data/WHO-COVID-19-global-data.csv'
REGION_DATA_PATH = './data/region.csv'
POPULATION_DATA_PATH = './data/populations.csv'
POPULATION_NORMALIZER = 1000000


class DataProcessor:
    """
      This class is responsible for importing, preprocessing, and processing
      the COVID-19 data. It includes methods to calculate Rt, normalize data,
      and append dataframes.
      """
    def __init__(self):
        self.df = None
        self.regions = None
        self.population = None

    def import_data(self):
        """
        Imports COVID-19 data from CSV files.
        """
        # Import the COVID-19 data from WHO-COVID-19-global-data.csv
        self.df = pd.read_csv(DATA_PATH)

        # Get 3-letter country code from 'regions.csv'
        self.regions = pd.read_csv(REGION_DATA_PATH)

        # Get population per country from World Bank
        self.population = pd.read_csv(POPULATION_DATA_PATH)

    def preprocess_data(self):
        """
        Preprocesses the imported data by merging and cleaning.
        """
        self.df['Date_reported'] = pd.to_datetime(self.df['Date_reported'])
        self.df = pd.merge(
            self.df,
            self.regions[['alpha-2', 'alpha-3']],
            left_on='Country_code',
            right_on='alpha-2')
        self.population['population'] = np.divide(
            (self.population['2019 [YR2019]'] +
             self.population['2020 [YR2020]'] +
             self.population['2021 [YR2021]']), 3.0)
        self.df = pd.merge(
            self.df,
            self.population[['Country Code', 'population']],
            left_on='alpha-3',
            right_on='Country Code')
        # Replace missing values by 0
        self.df = self.df.fillna(0)
        # Drop unnecessary columns
        self.df = self.df.drop(columns=['alpha-2', 'alpha-3', 'Country Code'])

    def calculate_rt(self, df):
        """
        Calculate Rt numbers for each country.
        """
        # Use the approximation: Rt = n(t) / n(t-1),
        # where n(t) is new infected at time t.
        # The approximation is from:
        # https://medium.com/@m.pierini/time-varying-reproduction-number-rt-theory-and-
        # python-implementation-part-i-basics-and-epiestim-99ea5fc30f51
        df['Rt'] = df['New_cases'] / df['New_cases'].shift(1)

        # Fill rt for new occurrences with number rt number of next day
        # (possible changing approach later)
        # different approach df['New_cases'] to be determined later
        df.loc[df['Rt'] == np.inf, 'Rt'] = df['Rt'].shift(-1)

        if df['New_cases'].iloc[0] != 0:
            df['Rt'].iloc[0] = df['Rt'].iloc[1]

        # Fill rest with 0
        df['Rt'] = df['Rt'].fillna(0)

        return df

    def calculate_deaths_per_cases(self, df):
        """
        Calculate deaths per cases for each country.
        """
        df['deaths_per_cases'] = df['Cumulative_deaths'] / df['Cumulative_cases']
        df['deaths_per_cases'] = df['deaths_per_cases'].fillna(0)
        return df

    def calc_stats(self, df, for_whom):
        """
        Calculate stats related to COVID-19 cases and deaths.
        """
        # Compute deaths per cases (stat 1)
        df = self.calculate_deaths_per_cases(df)

        # Number of cases (stat 2) is the column 'New_cases' and
        # number of deaths (stat 4) is the column 'New_deaths'
        # Compute rt number (stat 6)
        df['Rt'] = 0
        df = df.groupby(for_whom, group_keys=True).apply(self.calculate_rt)

        # Create a new dataframe for normalized data for stats 3 and 5
        df_norm = self.normalize(df)
        return df, df_norm

    def normalize(self, df):
        """
        Normalizes the data according to population size and
        scales it up to cases or deaths per 1000000 inhabitants.
        """
        df_norm = df.copy()
        cols_normalize = ['New_cases', 'Cumulative_cases', 'New_deaths', 'Cumulative_deaths']

        df_norm[cols_normalize] = (df_norm[cols_normalize].div(df_norm['population'], axis=0) *
                                   POPULATION_NORMALIZER)

        return df_norm

    def append_dataframes(self, df, df_regions):
        """
        Appends two dataframes containing Covid data for countries and regions.
        """
        # Appends the two dataframes together
        df = df.set_index(['Country', 'Date_reported'])
        df_regions = df_regions.reset_index(level=[1])
        df = df._append(df_regions)

        # Flattens the dataframe
        df = df.reset_index()
        return df


class CovidDashboard:
    """
    This class sets up and runs a Dash application to visualize COVID-19 data.
    """
    def __init__(self):
        self.processor = DataProcessor()
        self.processor.import_data()
        self.processor.preprocess_data()
        self.df, self.df_norm = self.processor.calc_stats(
            self.processor.df, 'Country')
        columns_to_sum = ['New_cases', 'Cumulative_cases',
                          'New_deaths', 'Cumulative_deaths',
                          'population']
        df_regions = self.processor.df.groupby(
            ['WHO_region', 'Date_reported'])[columns_to_sum].sum()
        df_regions, df_regions_norm = self.processor.calc_stats(df_regions, 'WHO_region')
        self.df = self.processor.append_dataframes(self.df, df_regions)
        self.app = dash.Dash(__name__)
        self.app.layout = self.create_layout()

    def create_layout(self):
        """
        Creates the layout of the Dash application.
        Returns:
        Dash layout
        """
        return html.Div([
            html.H1('Covid-19'),
            html.Div(
                [html.Label('Select Country'),
                 dcc.Dropdown(
                     id='country-dropdown',
                     options=[{'label': country, 'value': country} for
                              country in self.df['level_0'].unique()],
                     value=['Switzerland'],  # Default value
                     multi=True
                 ),
                 html.Label('Select timeframe: '),
                 dcc.DatePickerRange(
                     id='date-picker',
                     start_date=self.df['Date_reported'].min(),
                     end_date=self.df['Date_reported'].max(),
                     display_format='MM/YYYY', ),
                 html.Label('Normalize Data: '),
                 dcc.Checklist(
                     id='normalize-checklist',
                     options=[
                         {'label': 'Normalize', 'value': 'normalize'}
                     ],
                     value=['normalize']
                 ),

                 ], id='control-container', style={'display': 'flex', 'flex-direction': 'row'}),

            html.Div([
                dcc.Graph(id='cases-graph'),
                dcc.Graph(id='deaths-graph'),
            ], style={'display': 'flex', 'flex-direction': 'row'}),
        ])

    def generate_line_plot(self, df, selected_countries, data_col):
        """
        Creates a line graph illustrating the development of a specified data column
        (e.g. Cases, Deaths) over a period of time.
        Parameters:
        - df (dataframe) : dataframe containing values within date range
        - selected_countries (list): list of countries for which the user selected
        - data_col (str): name of the column for which values the line graph will be plotted
        Returns:
        - fig (plotly.graph_objects.Figure):
        line graph showing development of value in specified column
        """

        fig = go.Figure()
        # Sets name for graph title and axis title
        name_of_graph = data_col.replace('_', ' ').replace('New ', '').capitalize()


        # Adds for every selected country a line
        for country in selected_countries:
            selected_country_data  = df[df['level_0'] == country]
            fig.add_trace(go.Scatter(x=selected_country_data['Date_reported'],
                                     y=selected_country_data[data_col], mode='lines', name=country))

        # Sets the title and the axis titles of the graph
        fig.update_layout(title=f'{name_of_graph} by Country', yaxis_title=f'# of {name_of_graph}')
        return fig
    def register_callbacks(self):
        """
        Registers the callbacks for the Dash application.
        """
        @self.app.callback(
            [Output('cases-graph', 'figure'),
             Output('deaths-graph', 'figure')],
            [Input('country-dropdown', 'value'),
             Input('date-picker', 'start_date'),
             Input('date-picker', 'end_date'),
             Input('normalize-checklist', 'value')]
        )
        def update_graphs(selected_countries, start_date, end_date, normalize_value):
            # filter so only within given time range cases and deaths computed
            df_filtered = self.df[(self.df['Date_reported'] >= start_date) &
                                  (self.df['Date_reported'] <= end_date)]

            # Normalize data if requested
            if 'normalize' in normalize_value:
                df_filtered = self.processor.normalize(df_filtered)
            else:
                pass  # Data remains unchanged

            # graph showing number of cases over selected time period
            fig_cases = self.generate_line_plot(df_filtered, selected_countries, "New_cases")

            # graph showing number of deaths over selected time period
            fig_deaths = self.generate_line_plot(df_filtered, selected_countries, "New_deaths")

            return fig_cases, fig_deaths

    def run(self):
        """
        Run the app
        """
        self.register_callbacks()
        self.app.run_server(debug=True)


if __name__ == '__main__':
    dashboard = CovidDashboard()
    dashboard.run()
