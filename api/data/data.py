# Script python pour la génération des prédictions à une date donnée :
# - Si nécessaire, télécharger les données manquantes (plus récentes) et les
# sauvegarder dans la base de données,

import pandas as pd
import numpy as np
import openmeteo_requests
import requests_cache
from retry_requests import retry
import sqlite3

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Connect to SQLLITE database
conn = sqlite3.connect('weather.db')
cursor = conn.cursor()

# create tables if they don't exist

# first table contains all the original data
cursor.execute(''' CREATE TABLE IF NOT EXISTS weather(date_time, temperature_2m, dew_point_2m) ''')

# second table contains the training data
cursor.execute('''CREATE TABLE IF NOT EXISTS training(date_time, temperature_2m, dew_point, month, year, day)''') #TODO: adapt to real additional variables used

# third table contains the prediction label, the true label and the rmse score
cursor.execute(''' CREATE TABLE IF NOT EXISTS predictions(date_time, pred_temperature_2m, true_temperature_2m, rmse, model_id) ''')


# Example parameters
url = "https://archive-api.open-meteo.com/v1/archive"
params = { # Strasbourg
	"latitude": 48.5839,
	"longitude": 7.7455,
	"start_date": "2020-01-01",
	"end_date": "2023-12-31",
	"hourly": "temperature_2m",
	"timezone": "America/New_York"
}

def get_data(url, params, column_name):
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    hourly = response.Hourly()
    hourly_column_name = hourly.Variables(0).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}
    hourly_data[column_name] = hourly_column_name

    df = pd.DataFrame(data = hourly_data)

    df.set_index('date', inplace=True)
    df_resampled = df.resample('3h').mean()

    return df_resampled


def save_to_db(df):
    # dataframe to save
    df = df.copy()
    
    df.to_sql(name='weather', # Name of SQL Table
              con=conn, # sqlite3.Connection
              if_exists='replace', # drop the table before inserting new values. Means that i get all the data at all times
              index=True, # DF index is date_time
              index_label="date_time"  
            )
    
    conn.commit()


    return "Data saved to database"


def test_db():
    rows = cursor.execute("SELECT * FROM weather LIMIT 5").fetchall()

    return rows


if __name__ == '__main__':
    df = get_data(url, params, "temperature_2m")
    message = save_to_db(df)
    print(f'message: {message}')
    
    # verify db
    print(test_db())
    conn.close()