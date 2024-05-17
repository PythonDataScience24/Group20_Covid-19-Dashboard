import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import plotly.express as px

class CovidDashboard:
    """
    This class sets up and runs a Dash application to visualize COVID-19 data.
    """
    def __init__(self):
        self.df_absolute = pd.read_csv('./processed_data/df_absolute.csv')
        self.df_normalized = pd.read_csv('./processed_data/df_normalized.csv')
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
                     value=['Switzerland'],  # Default value
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
                dcc.Graph(id='deaths-graph'),
            ], style={'display': 'flex', 'flex-direction': 'row'}),
            dcc.Graph(id='choropleth-map')
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
            selected_country_data = df[df['Country_region'] == country]
            fig.add_trace(go.Scatter(x=selected_country_data['Date_reported'],
                                     y=selected_country_data[data_col], mode='lines', name=country))

        # Sets the title and the axis titles of the graph
        fig.update_layout(title=f'{name_of_graph} by Country', yaxis_title=f'# of {name_of_graph}')
        return fig

    def generate_choropleth_map(self, df, data_col):
        """
        Generates a choropleth map showing the distribution of a specified data column globally.
        Parameters:
        - df (dataframe) : dataframe containing values to be visualized
        - data_col (str): name of the column for which values the choropleth map will be plotted
        Returns:
        - fig (plotly.graph_objects.Figure):
        choropleth map showing the global distribution of the specified data column
        """
        fig = px.choropleth(
            df,
            locations="Country_region",
            locationmode='country names',
            color=data_col,
            hover_name="Country_region",
            color_continuous_scale=px.colors.sequential.Plasma,
            title=f'Global distribution of {data_col.replace("_", " ").capitalize()}'
        )
        return fig

    def register_callbacks(self):
        """
        Registers the callbacks for the Dash application.
        """
        @self.app.callback(
            [Output('cases-graph', 'figure'),
             Output('deaths-graph', 'figure'),
             Output('choropleth-map', 'figure')],
            [Input('country-dropdown', 'value'),
             Input('date-picker', 'start_date'),
             Input('date-picker', 'end_date'),
             Input('normalize-checklist', 'value')]
        )
        def update_graphs(selected_countries, start_date, end_date, normalize_value):
            # Normalize data if requested
            if 'normalize' in normalize_value:
                df_selected = self.df_normalized
            else:
                df_selected = self.df_absolute

            # filter so only within given time range cases and deaths computed
            df_selected = df_selected[(df_selected['Date_reported'] >= start_date) &
                                      (df_selected['Date_reported'] <= end_date)]

            # graph showing number of cases over selected time period
            fig_cases = self.generate_line_plot(df_selected, selected_countries, "New_cases")

            # graph showing number of deaths over selected time period
            fig_deaths = self.generate_line_plot(df_selected, selected_countries, "New_deaths")

            # choropleth map showing global distribution of cumulative cases
            fig_choropleth = self.generate_choropleth_map(df_selected, "Cumulative_cases")

            return fig_cases, fig_deaths, fig_choropleth

    def run(self):
        """
        Run the app
        """
        self.register_callbacks()
        self.app.run_server(debug=True)


if __name__ == '__main__':
    dashboard = CovidDashboard()
    dashboard.run()
