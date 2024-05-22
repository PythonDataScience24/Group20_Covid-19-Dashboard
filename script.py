"""
This module contains a dashboard application for visualizing COVID-19 data.
It includes the dashboard itself and methods for visualizing the data using Dash.
"""
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import plotly.express as px
import data_prep


class Visualisation:
    """
    This is a class containing different functions for creating plots out of data.
    """
    def __init__(self):
        self.processor = data_prep.DataProcessor()

    def generate_plots(self, df_filtered, selected):
        """
        Generates line and bar plots for selected data and countries.
        """
        fig_cases = self.generate_line_plot(df_filtered, selected, "New_cases")
        fig_deaths = self.generate_line_plot(df_filtered, selected, "New_deaths")
        rt_plot = self.plot_bar(df_filtered, selected, "Rt")
        death_cases_plot = self.plot_bar(df_filtered, selected, "deaths_per_cases")

        return fig_cases, fig_deaths, rt_plot, death_cases_plot

    def generate_line_plot(self, df, selected_countries, data_col):
        """
        Creates a line graph illustrating the development of a specified data column.
        """
        fig = go.Figure()
        name_of_graph = data_col.replace('_', ' ').replace('New ', '').capitalize()

        for country in selected_countries:
            selected_country_data = df[df['Country_region'] == country]
            fig.add_trace(go.Scatter(x=selected_country_data['Date_reported'],
                                     y=selected_country_data[data_col], mode='lines', name=country))

        fig.update_layout(title=f'{name_of_graph} by Country', yaxis_title=f'# of {name_of_graph}',
                          font=dict(family='Arial', size=16, color='#7f7f7f'),
                          plot_bgcolor='white', paper_bgcolor='white'
                          )
        return fig

    def plot_bar(self, df, selected_countries, data_col):
        """
        Generates a bar plot for the given data column for the selected countries.
        """
        fig = go.Figure()
        df, title = self.compute_data(df, data_col)

        for country_region in selected_countries:
            selected_country_data = df[df['Country_region'] == country_region]
            fig.add_trace(go.Bar(x=selected_country_data['Country_region'],
                                 y=selected_country_data[data_col],
                                 name=country_region))

        fig.update_layout(
            title=title,
            font=dict(family='Arial', size=16, color='#7f7f7f'),
            plot_bgcolor='white', paper_bgcolor='white'
        )
        return fig

    def compute_data(self, df, data_col):
        """
        Returns the title and the data for a bar plot based on the data column.
        """
        title = ""
        grouped = df.groupby('Country_region')

        if data_col == 'Rt':
            title = 'Average Rt number (Transmission rate)'
            df = grouped.agg({data_col: 'mean'}).reset_index()
        elif data_col == 'deaths_per_cases':
            title = 'Deaths per cases'
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
        try:
            self.df_absolute = pd.read_csv('./processed_data/df_absolute.csv')
            self.df_normalized = pd.read_csv('./processed_data/df_normalized.csv')
        except FileNotFoundError as e:
            print(f"Error: {e}. Ensure that the required CSV files are in the 'processed_data' directory.")
            self.df_absolute = pd.DataFrame()
            self.df_normalized = pd.DataFrame()
        except pd.errors.EmptyDataError as e:
            print(f"Error: {e}. The CSV files are empty. Please provide valid data.")
            self.df_absolute = pd.DataFrame()
            self.df_normalized = pd.DataFrame()
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            self.df_absolute = pd.DataFrame()
            self.df_normalized = pd.DataFrame()

        self.visualize = Visualisation()
        self.app = dash.Dash(__name__)
        self.app.layout = self.create_layout()

    def create_layout(self):
        """
        Creates the layout of the Dash application.
        """
        return html.Div([
            html.H1('COVID-19 Dashboard', style={'textAlign': 'center', 'color': '#003366'}),
            html.Div(
                [html.Div(
                    [html.Label('Select Country', style={'fontWeight': 'bold'}),
                     dcc.Dropdown(
                         id='country-dropdown',
                         options=[{'label': country, 'value': country} for
                                  country in self.df_absolute['Country_region'].unique()],
                         value=['Switzerland', 'EURO', 'Türkiye'],
                         multi=True,
                         style={'width': '100%'}
                     ),
                     ],
                    style={'flex': '1', 'margin-right': '10px'}
                ),
                    html.Div(
                        [html.Label('Select Timeframe', style={'fontWeight': 'bold'}),
                         dcc.DatePickerRange(
                             id='date-picker',
                             start_date=self.df_absolute['Date_reported'].min(),
                             end_date=self.df_absolute['Date_reported'].max(),
                             display_format='MM/YYYY',
                             style={'width': '100%'}
                         ),
                         ],
                        style={'flex': '1', 'margin-right': '10px'}
                    ),
                    html.Div(
                        [html.Label('Normalize Data', style={'fontWeight': 'bold'}),
                         dcc.Checklist(
                             id='normalize-checklist',
                             options=[{'label': 'Normalize', 'value': 'normalize'}],
                             value=['normalize'],
                             style={'margin-top': '10px'}
                         ),
                         ],
                        style={'flex': '1'}
                    )
                ],
                id='control-container',
                style={'display': 'flex', 'flex-direction': 'row', 'padding': '10px'}
            ),
            html.Div([
                html.Div([
                    dcc.Graph(id='cases-graph', style={'width': '100%', 'display': 'inline-block'}),
                    dcc.Graph(id='deaths-graph', style={'width': '100%', 'display': 'inline-block'}),
                ], style={'width': '48%', 'display': 'inline-block', 'vertical-align': 'top'}),
                html.Div([
                    dcc.Graph(id='rt-graph', style={'width': '100%', 'display': 'inline-block'}),
                    dcc.Graph(id='deaths-per-cases-graph', style={'width': '100%', 'display': 'inline-block'}),
                ], style={'width': '48%', 'display': 'inline-block', 'vertical-align': 'top'}),
            ], style={'display': 'flex', 'justify-content': 'space-between'}),
        ], style={'font-family': 'Arial, sans-serif', 'backgroundColor': '#f9f9f9', 'padding': '20px'})

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
            if 'normalize' in normalize_value:
                df_filtered = self.df_normalized
            else:
                df_filtered = self.df_absolute

            df_filtered = df_filtered[(df_filtered['Date_reported'] >= start_date) &
                                      (df_filtered['Date_reported'] <= end_date)]

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
