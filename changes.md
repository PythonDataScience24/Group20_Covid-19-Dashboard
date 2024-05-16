# Restructure code

Since the script.py module was very complex and the components were unnecessarily heaviliy coupled we
decided to separate it into two python modules (data processing (data_prep.py), and the dash app) 
and two data folders for now.

In the data_prep.py module we process the data and compute dataframes for absolute and normalized COVID-data.
The dataframes are then saved as separate files.

In the script.py module we then access those computed COVID-dataframes and visualize them using dash.

This approach has the advantage that we don't have to compute the data every time we run the app. This was unnessary
since the COVID-data is not updated within our programm. If it would be updated, we could simply initialize a Data_Processor
within the the CovidDashboard.

Additionally it decluttered the CovidDashboard constructor. This made the code more comprehensible and promoted loose coupling 
between the components which makes the code easier to maintain in the long run.

In the future we will create a separate static class for visualisation to encapuslate all the functions relating
to visualizing the data. But for now we decided to keep it within the CovidDashboard class since its comprehensible
and maintaible.

It remains open whether we want to create a separate module with which the script.py component interacts or just a class within the
script.py module. 

If they are tightly coupled, putting them into separate classes within the same module could make sense. 
This approach keeps related functionality organized together.

However, if the components (visualization, and the dash app) are fairly independent and can be reused or extended separately, 
creating three separate modules might be more modular and maintainable in the long run. This would allow for easier testing, debugging,
and reuse of each component. (likely this approach)

Previously the code was already separated into different methods to promote reusability.

# Abstraction

In the class DataProcessor() we treat regional and country data as COVID-data (= the same).







