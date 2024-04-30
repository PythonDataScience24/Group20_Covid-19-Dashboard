import pandas as pd
import numpy as np
import seaborn as sns

def calc_rt(x):
    """
    Calculate Rt numbers for each country.

    Parameter: 
        x: df containing Covid19 data
    Returns:
        x: df with calculated rt number
    """
    x['Rt'] = x['New_cases'].shift(-1)/x['New_cases']

    # Forward second last value to last value
    x['Rt'].iloc[-1] = x['Rt'].iloc[-2] # probably change in future but for now good
    # Fill rest with 0 for now
    x['Rt'].fillna(0, inplace= True)

    return x

def normalize(df):
    """
    Normalizes the data according to population size and scales it up to cases or deaths per 1000000 inhabitants.
    Important for statistics 3 and 5.

    Parameter:
        df_norm: df containing Covid19 data
    Returns:
        df_norm: df with normalized Case numbers and deaths per 1000000
    """
    df_norm = df.copy()
    cols_normalize = ['New_cases', 'Cumulative_cases', 'New_deaths', 'Cumulative_deaths']

    df_norm[cols_normalize] = df_norm[cols_normalize].div(df_norm['population'], axis=0)
    df_norm[cols_normalize] = np.multiply(df_norm[cols_normalize], 1000000)

    return df_norm


def main(): 
    ########################
    # Import the data
    ########################

    df = pd.read_csv('./data/WHO-COVID-19-global-data.csv')

    df['Date_reported'] = pd.to_datetime(df['Date_reported'])


    # get 3-letter country code from 'regions.csv', data from a previous exercise.
    # we need the 3-letter code to join with the population data
    regions = pd.read_csv('./data/region.csv')
    df = pd.merge(df, regions[['alpha-2', 'alpha-3']], left_on='Country_code', right_on='alpha-2')

    # get population per country from a manual CSV export from the world bank:
    # https://databank.worldbank.org/source/population-estimates-and-projections#
    population = pd.read_csv('./data/d55c23f8-6bb7-4016-88b8-08519f13065e_Data.csv')
    # for simplicity, use a static population number: the average population between 2019 and 2021
    population['population'] = np.divide((population['2019 [YR2019]'] + population['2020 [YR2020]'] + population['2021 [YR2021]']), 3.0)

    df = pd.merge(df, population[['Country Code', 'population']], left_on='alpha-3', right_on='Country Code')


    ########################
    # Preprocess data
    ########################

    # Replace missing values by 0
    df.fillna(0, inplace = True)

    # Drop unnecessary columns
    df.drop(columns=['alpha-2', 'alpha-3', 'Country Code'], inplace=True)


    ########################
    # Compute statistics
    ########################

    # statistic 1: deaths per cases
    df['deaths_per_cases'] = df['Cumulative_deaths'] / df['Cumulative_cases']
    df['deaths_per_cases'].fillna(0, inplace = True) # fix division by zero error

    # statistic 2: number of cases is the column 'New_cases'

    # statistic 3: number of cases (normalized) calculated in separate df_norm

    # statistic 4: number of deaths is the column 'New_deaths'

    # statistic 5: number of deaths (normalized) calculated in separate df_norm

    # statistic 6: the Rt number
    # use the approximation: Rt = n(t) / n(t-1), where n(t) is new infected at time t. the approximation is from:
    # https://medium.com/@m.pierini/time-varying-reproduction-number-rt-theory-and-python-implementation-part-i-basics-and-epiestim-99ea5fc30f51
    # compute Rt 
    country = 'CH'
    # TO DO: find out how missing values handled most reasonable
    df['Rt'] = 0
    df = df.groupby('Country').apply(calc_rt)


    
    # Creates a new dataframe with normalized values according to population size
    df_norm = normalize(df)

    print(df[df['Country_code'] == country])
    print(df_norm[df_norm['Country_code'] == country])


if(__name__ == '__main__'):
    main()