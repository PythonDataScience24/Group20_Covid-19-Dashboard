import pandas as pd
import numpy as np

# constants
data_path = './data/WHO-COVID-19-global-data.csv'
region_data_path = './data/region.csv'
population_data_path = './data/populations.csv'
population_normalizer = 1000000


def import_data():
    # import the covid 19 data from WHO-COVID-19-global-data.csv
    df = pd.read_csv(data_path)

    # we need the 3-letter code to join with the population data
    # get 3-letter country code from 'regions.csv', data from a previous exercise.
    regions = pd.read_csv(region_data_path)

    # get population per country from a manual CSV export from the world bank:
    # https://databank.worldbank.org/source/population-estimates-and-projections#
    # for simplicity, use a static population number: the average population between 2019 and 2021
    population = pd.read_csv(population_data_path)

    return df, regions, population


def preprocess_data(df, regions, population):
    df['Date_reported'] = pd.to_datetime(df['Date_reported'])
    df = pd.merge(df, regions[['alpha-2', 'alpha-3']], left_on='Country_code', right_on='alpha-2')
    population['population'] = np.divide(
        (population['2019 [YR2019]'] + population['2020 [YR2020]'] + population['2021 [YR2021]']), 3.0)
    df = pd.merge(df, population[['Country Code', 'population']], left_on='alpha-3', right_on='Country Code')
    # Replace missing values by 0
    df.fillna(0, inplace=True)
    # Drop unnecessary columns
    df.drop(columns=['alpha-2', 'alpha-3', 'Country Code'], inplace=True)
    return df

def calculate_rt(df):
    """
    Calculate Rt numbers for each country.

    Parameter: 
        df (DataFrame): df containing Covid19 data

    Returns :
        df (DataFrame): df with calculated rt number
    """
    # use the approximation: Rt = n(t) / n(t-1), where n(t) is new infected at time t. the approximation is from:
    # https://medium.com/@m.pierini/time-varying-reproduction-number-rt-theory-and-python-implementation-part-i-basics-and-epiestim-99ea5fc30f51
    df['Rt'] = df['New_cases']/df['New_cases'].shift(1)

    # Fill rt for new occurences with number rt number of next day (possible changing approach later) 
    df.loc[df['Rt'] == np.inf, 'Rt'] = df['Rt'].shift(-1) # different approach df['New_cases'] to be determined later
    
    if(df['New_cases'].iloc[0] != 0):
        df['Rt'].iloc[0] = df['Rt'].iloc[1]


    # Fill rest with 0 
    df['Rt'].fillna(0, inplace=True)
    

    return df


def calculate_deaths_per_cases(df):

    df['deaths_per_cases'] = df['Cumulative_deaths'] / df['Cumulative_cases']
    df['deaths_per_cases'].fillna(0, inplace=True)
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

    # number of cases (stat 2) is the column 'New_cases' and number of deaths (stat 4) is the column 'New_deaths'

    # Compute rt number (stat 6)
    df['Rt'] = 0
    df = df.groupby(for_whom).apply(calculate_rt)


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


def main():
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


    country = 'CH'
    # print absolute data for specific country
    print(df[df['Country_code'] == country])
    # print normalized data for specific country
    print(df_norm[df_norm['Country_code'] == country])

    region = 'EURO'
    # print absolute data for region (in this case Europe)
    print(df_regions.loc[region])
    # print normalized data for region (in this case Europe)
    print(df_regions_norm.loc[region])


if(__name__ == '__main__'):
    main()