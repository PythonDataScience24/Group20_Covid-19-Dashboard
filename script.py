import pandas as pd

df = pd.read_csv('./data/WHO-COVID-19-global-data.csv')

# get 3-letter country code from 'regions.csv', data from a previous exercise.
# we need the 3-letter code to join with the population data
regions = pd.read_csv('./data/region.csv')
merged1 = df.merge(regions[['alpha-2', 'alpha-3']], left_on='Country_code', right_on='alpha-2')

# get population per country from a manual CSV export from the world bank:
# https://databank.worldbank.org/source/population-estimates-and-projections#
population = pd.read_csv('./data/d55c23f8-6bb7-4016-88b8-08519f13065e_Data.csv')
# for simplicity, use a static population number: the average population of 2019 and 2020
population['population'] = (population['2019 [YR2019]'] + population['2019 [YR2019]']) * 2.0

merged = merged1.merge(population[['Country Code', 'population']], left_on='alpha-3', right_on='Country Code')

