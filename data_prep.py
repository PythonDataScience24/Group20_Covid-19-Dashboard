"""
This module contains the data processing for the COVID-19 data.
It includes processing, normalization, and saving the data within a folder.
"""
import pandas as pd
import numpy as np

# Constants
DATA_PATH = './raw_data/WHO-COVID-19-global-data.csv'
REGION_DATA_PATH = './raw_data/region.csv'
POPULATION_DATA_PATH = './raw_data/populations.csv'
POPULATION_NORMALIZER = 1000000


class DataProcessor:
    """
    This class is responsible for importing and processing the COVID-19 data.
    It stores abssolute and normalized Covid-data and includes methods to
    calculate statistics, normalize data and to append dataframes.
    """
    def __init__(self, for_whom):
        self.df_abs = None
        self.df_norm = None
        self.initialize_data(for_whom)

    def initialize_data(self, for_whom):
        """
        Imports, processes and computes the data for countries or regions.
        """
        self.import_data()
        self.preprocess_data()

        if for_whom == 'WHO_region':
            self.compute_regional_df()
        self.calc_stats(for_whom)


    def import_data(self):
        """
        Imports COVID-19 data from CSV files.
        """
        # Import the COVID-19 data from WHO-COVID-19-global-data.csv
        self.df_abs = pd.read_csv(DATA_PATH)

        # Get 3-letter country code from 'regions.csv'
        self.regions = pd.read_csv(REGION_DATA_PATH)

        # Get population per country from World Bank
        self.population = pd.read_csv(POPULATION_DATA_PATH)

    def preprocess_data(self):
        """
        Preprocesses the imported data by merging and cleaning.
        """
        self.df_abs['Date_reported'] = pd.to_datetime(self.df_abs['Date_reported'])
        self.df_abs = pd.merge(
            self.df_abs,
            self.regions[['alpha-2', 'alpha-3']],
            left_on='Country_code',
            right_on='alpha-2')
        self.population['population'] = np.divide(
            (self.population['2019 [YR2019]'] +
             self.population['2020 [YR2020]'] +
             self.population['2021 [YR2021]']), 3.0)
        self.df_abs = pd.merge(
            self.df_abs,
            self.population[['Country Code', 'population']],
            left_on='alpha-3',
            right_on='Country Code')
        # Replace missing values by 0
        self.df_abs = self.df_abs.fillna(0)
        # Drop unnecessary columns
        self.df_abs = self.df_abs.drop(columns=['alpha-2', 'alpha-3', 'Country Code'])

    def calculate_rt(self, df_covid):
        """
        Calculate Rt numbers.
        """
        # Use the approximation: Rt = n(t) / n(t-1),
        # where n(t) is new infected at time t.
        # The approximation is from:
        # https://medium.com/@m.pierini/time-varying-reproduction-number-rt-theory-and-
        # python-implementation-part-i-basics-and-epiestim-99ea5fc30f51
        df_covid['Rt'] = df_covid['New_cases'] / df_covid['New_cases'].shift(1)

        # Fill rt for new occurrences with number rt number of next day
        # (possible changing approach later)
        # different approach df['New_cases'] to be determined later
        df_covid.loc[df_covid['Rt'] == np.inf, 'Rt'] = df_covid['Rt'].shift(-1)

        if df_covid['New_cases'].iloc[0] != 0:
            df_covid['Rt'].iloc[0] = df_covid['Rt'].iloc[1]

        # Fill rest with 0
        df_covid['Rt'] = df_covid['Rt'].fillna(0)

        return df_covid


    def calculate_deaths_per_cases(self):
        """
        Calculate deaths per cases.
        """
        self.df_abs['deaths_per_cases'] = self.df_abs['Cumulative_deaths'] / self.df_abs['Cumulative_cases']
        self.df_abs['deaths_per_cases'] = self.df_abs['deaths_per_cases'].fillna(0)

    def calc_stats(self, for_whom):
        """
        Calculate stats related to COVID-19 cases and deaths.
        """
        # Compute deaths per cases (stat 1)
        self.calculate_deaths_per_cases()

        # Number of cases (stat 2) is the column 'New_cases' and
        # number of deaths (stat 4) is the column 'New_deaths'
        # Compute rt number (stat 6)
        self.df_abs['Rt'] = 0
        self.df_abs = self.df_abs.groupby(for_whom).apply(self.calculate_rt)

        # Create a new dataframe for normalized data for stats 3 and 5
        self.df_norm = self.normalize()

    def normalize(self):
        """
        Normalizes the data according to population size and
        scales it up to cases or deaths per 1000000 inhabitants.
        """
        self.df_norm = self.df_abs.copy()
        cols_normalize = ['New_cases', 'Cumulative_cases', 'New_deaths', 'Cumulative_deaths']

        self.df_norm[cols_normalize] = (self.df_norm[cols_normalize].div(
                                    self.df_norm['population'], axis=0) * POPULATION_NORMALIZER)

        return self.df_norm

    def compute_regional_df(self):
        """
        Creates a dataframe COVID-19 by WHO region.
        """
        columns_to_sum = ['New_cases', 'Cumulative_cases',
                        'New_deaths', 'Cumulative_deaths',
                        'population']
        self.df_abs = self.df_abs.groupby(
            ['WHO_region', 'Date_reported'])[columns_to_sum].sum().reset_index()


    def append_dataframes(self, df_countries, df_regions):
        """
        Appends two dataframes containing Covid data for countries and regions.
        """
        relevant = ['Country_region', 'Date_reported', 'New_cases',
                    'Cumulative_cases', 'New_deaths', 'Cumulative_deaths',
                    'deaths_per_cases', 'Rt']
        # Append the two dataframes together
        df_countries = df_countries.rename(columns={'Country': 'Country_region'})
        df_regions = df_regions.rename(columns={'WHO_region': 'Country_region'})
        df_covid = pd.concat([df_countries, df_regions], ignore_index=True)

        # Select relevant information
        df_covid = df_covid[relevant]
        return df_covid

    def get_data(self):
        """
        Returns absolute and normalized Covid data.
        """
        return self.df_abs, self.df_norm


def main():
    """
    Creates dataframes for absoulute and normalized COVID-data
    and save them in the folder processed_data.
    """

    # Compute absolute and normalized dataframes for countries and regions
    covid_countries = DataProcessor('Country')
    covid_regions = DataProcessor('WHO_region')

    df_countries, df_countries_norm = covid_countries.get_data()
    df_regions, df_regions_norm = covid_regions.get_data()

    # Append dataframes countries and regions together
    df_absolute = covid_countries.append_dataframes(df_countries, df_regions)
    df_normalized = covid_countries.append_dataframes(df_countries_norm, df_regions_norm)

    # Save absolute and normalized data to CSV
    df_absolute.to_csv('processed_data/df_absolute.csv', index=False)
    df_normalized.to_csv('processed_data/df_normalized.csv', index=False)

if __name__ == '__main__':
    main()
