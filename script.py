import pandas as pd
import seaborn as sns

########################
# Import the data
########################

df = pd.read_csv('./data/WHO-COVID-19-global-data.csv')
df['Date_reported'] = pd.to_datetime(df['Date_reported'])

# get 3-letter country code from 'regions.csv', data from a previous exercise.
# we need the 3-letter code to join with the population data
regions = pd.read_csv('./data/region.csv')
merged1 = df.merge(regions[['alpha-2', 'alpha-3']], left_on='Country_code', right_on='alpha-2')

# get population per country from a manual CSV export from the world bank:
# https://databank.worldbank.org/source/population-estimates-and-projections#
population = pd.read_csv('./data/d55c23f8-6bb7-4016-88b8-08519f13065e_Data.csv')
# for simplicity, use a static population number: the average population between 2019 and 2021
population['population'] = (population['2019 [YR2019]'] + population['2020 [YR2020]'] + population['2021 [YR2021]']) / 3.0

df = merged1.merge(population[['Country Code', 'population']], left_on='alpha-3', right_on='Country Code')


########################
# Compute statistics
########################

# statistic 1: deaths per cases
df['deaths_per_cases'] = df['Cumulative_deaths'] / df['Cumulative_cases']

# statistic 2: number of cases is the column 'New_cases'

# statistic 3: number of cases (normalized)
df['New_cases_normalized'] = df['New_cases'] / df['population']

# statistic 4: number of deaths is the column 'New_deaths'

# statistic 5: number of deaths (normalized)
df['New_deaths_normalized'] = df['New_deaths'] / df['population']

# statistic 6: the Rt number
# use the approximation: Rt = n(t) / n(t-1), where n(t) is new infected at time t. the approximation is from:
# https://medium.com/@m.pierini/time-varying-reproduction-number-rt-theory-and-python-implementation-part-i-basics-and-epiestim-99ea5fc30f51
# compute Rt for a given country
country = 'CH'
df['Rt'] = df['New_cases'] / df['New_cases'].shift(-1)
filtered = df[df['Country_code'] == country]
sns.lineplot(data=filtered, y='Rt', x='Date_reported')
