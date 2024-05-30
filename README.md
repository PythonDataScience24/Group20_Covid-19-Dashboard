# COVID-19 Dashboard

## Running the program

Run the script `script.py` with python 3, without any args. Install the 
required modules in your virtual environment with `pip install -r requirements.txt`.

The application is a web app, and is viewable in the browser on http://127.0.0.1:8050/

## What the program currently does

The data is imported and simple statistics are calculated.

The dashboard allows the user to input different countries and regions and 
select a timeframe. 

According to the user input (a selection of countries, and a selected timeframe)
cases and deaths are plotted in line plots, and the average Rt number and
deaths per cases are plotted as bar plots (the average value over the
selected timeframe).

Additionally, the user can select whether the data should be normalized.

## Project Information

This project was completed as part of the Programming for Data Science 2024 class. 
Further development is not guaranteed.

The primary objective of this project is to compute simple statistics of COVID-19 infection data and 
provide visualizations that depict the trends of infections and deaths across various countries. 
This allows users to gain an insightful overview of the data.

It should act as a comparison tool for assessing the COVID-19 situation across different countries and
regions.
