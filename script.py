"""
This module contains a dashboard application for visualizing COVID-19 data.
It includes the dashboard itself and methods for visualizing the data using Dash.
"""
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import data_prep

class Visualisation:
    """
    This is a class containing different functions for creating plots out of data.
    """
    def __init__(self):
        self.processor = data_prep.DataProcessor()

    def generate_plots(self, df_filtered, selected):
        """
        Generates line and bar plots for selected data and and countries.
        """
        # Generate line plot for number of cases over selected time period
        fig_cases = self.generate_line_plot(df_filtered, selected, "New_cases")

        # Generate line plot for number of deaths over selected time period
        fig_deaths = self.generate_line_plot(df_filtered, selected, "New_deaths")

        # Generate bar plot for average Rt number for comparison of countries
        rt_plot = self.plot_bar(df_filtered, selected, "Rt")

        # Generate bar plot for deaths per cases for comparison of countries
        death_cases_plot = self.plot_bar(df_filtered, selected, "deaths_per_cases")

        return fig_cases, fig_deaths, rt_plot, death_cases_plot


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
            selected_country_data  = df[df['Country_region'] == country]
            fig.add_trace(go.Scatter(x=selected_country_data['Date_reported'],
                                     y=selected_country_data[data_col], mode='lines', name=country))

        # Sets the title and the axis titles of the graph
        fig.update_layout(title=f'{name_of_graph} by Country', yaxis_title=f'# of {name_of_graph}')
        return fig

    def plot_bar(self, df, selected_countries, data_col):
        """
        Generates a bar plot for the given data column for the selected countries.
        """
        fig = go.Figure()

        # Compute data and obtain title
        df, title = self.compute_data(df, data_col)

        # Add bars for each selected country or region
        for country_region in selected_countries:
            selected_country_data = df[df['Country_region'] == country_region]
            fig.add_trace(go.Bar(x=selected_country_data['Country_region'],
                                 y=selected_country_data[data_col],
                                 name=country_region
            ))

        # Update layout with title
        fig.update_layout(title=title)

        return fig

    def compute_data(self, df, data_col):
        """
        Returns the title and the data for a bar plot if column name and if the column
        is either Rt or death_per_cases it computes the data for the bar plot.
        """
        title = ""
        grouped = df.groupby('Country_region')

        if data_col == 'Rt':
            title = 'Average Rt number (Transmission rate)'
            # Group by country and calculate mean
            df = grouped.agg({data_col: 'mean'}).reset_index()
        elif data_col == 'deaths_per_cases':
            title = 'Deaths per cases'
            # Calculate deaths per cases and get the last element for each country
            df = grouped.apply(self.processor.calculate_deaths_per_cases).reset_index(drop=True)
            df = df.groupby('Country_region').tail(1)
        else:
            print(f"The column '{data_col}' either doesn't exist or we don't compute it yet.")

        return df, title


class CovidDashboard:
    """
    This class sets up and runs a Dash application to visualize COVID-19 data.
    """
    def __init__(self):
        self.df_absolute = pd.read_csv('./processed_data/df_absolute.csv')
        self.df_normalized = pd.read_csv('./processed_data/df_normalized.csv')
        self.visualize = Visualisation()
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
                              country in self.df_absolute['Country_region'].unique()],
                     value=['Switzerland', 'EURO', 'Türkiye'],  # Default value
                     multi=True
                 ),
                 html.Label('Select timeframe: '),
                 dcc.DatePickerRange(
                     id='date-picker',
                     start_date=self.df_absolute['Date_reported'].min(),
                     end_date=self.df_absolute['Date_reported'].max(),
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
                dcc.Graph(id='deaths-per-cases-graph')

            ], style={'display': 'flex', 'flex-direction': 'row'}),
            html.Div([
                dcc.Graph(id='deaths-graph'),
                dcc.Graph(id='rt-graph'),

            ], style={'display': 'flex', 'flex-direction': 'row'}),

        ])

    def register_callbacks(self):
        """
        Registers the callbacks for the Dash application.
        """
        @self.app.callback(
            [Output('cases-graph', 'figure'),
             Output('deaths-graph', 'figure'),
             Output('rt-graph', 'figure'),
             Output('deaths-per-cases-graph', 'figure')],
            [Input('country-dropdown', 'value'),
             Input('date-picker', 'start_date'),
             Input('date-picker', 'end_date'),
             Input('normalize-checklist', 'value')]
        )
        def update_graphs(selected, start_date, end_date, normalize_value):
            # Normalize data if requested
            if 'normalize' in normalize_value:
                df_filtered = self.df_normalized
            else:
                df_filtered = self.df_absolute

            # filter so only within given time range computed
            df_filtered = df_filtered[(df_filtered['Date_reported'] >= start_date) &
                                    (df_filtered['Date_reported'] <= end_date)]

            # Genreates two line and two bar plots for the dashboard
            fig_cases, fig_deaths, rt_plot, death_cases_plot = self.visualize.generate_plots(df_filtered, selected)


            return fig_cases, fig_deaths, rt_plot, death_cases_plot

    def run(self):
        """
        Run the app
        """
        self.register_callbacks()
        self.app.run_server(debug=True)


if __name__ == '__main__':
    dashboard = CovidDashboard()
    dashboard.run()
