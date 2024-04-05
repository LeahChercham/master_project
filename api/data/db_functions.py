# Script python pour la génération des prédictions à une date donnée :
# - Si nécessaire, télécharger les données manquantes (plus récentes) et les
# sauvegarder dans la base de données,

import pandas as pd
import numpy as np
import openmeteo_requests
import requests_cache
from retry_requests import retry
import sqlite3
import sys
import os
from datetime import datetime


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import commun

conn = None
cursor = None

def create_db_connection():
    print(40*'_')
    print()
    print("Creating connection...")
    global conn, cursor
    # Connect to SQLLITE database
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    
    print("Connection created successfully")
    return conn, cursor


# Database Tables
# weather: first table contains all the original data, the true labels from 01/01/2020 up until today
# training: second table contains the training data from 01/01/2020 up until 31/12/2023
# predictions: third table contains the prediction label, the true label and the rmse score : empty at first

# TODO: I dont think i need this: 
# cursor.execute(''' CREATE TABLE IF NOT EXISTS weather(date_time, temperature_2m, dew_point_2m) ''')
# cursor.execute('''CREATE TABLE IF NOT EXISTS training(date_time, temperature_2m, dew_point, month, year, day)''') #TODO: adapt to real additional variables used
# cursor.execute(''' CREATE TABLE IF NOT EXISTS predictions(date_time, pred_temperature_2m, true_temperature_2m, rmse, model_id) ''')


def get_data(url, params, column_names):
    print(40*'_')
    print()
    print("Getting data from Open Meteo API Client...")
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    hourly = response.Hourly()

    # Initialize dictionary to store hourly data for each variable
    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )}

    # Loop through each variable and retrieve corresponding data
    for column_name in column_names:
        # Get values for the current variable
        hourly_values = hourly.Variables(column_names.index(column_name)).ValuesAsNumpy()

        # Store values in the dictionary
        hourly_data[column_name] = hourly_values

    # Create DataFrame from the hourly data dictionary
    df = pd.DataFrame(data=hourly_data)

    # Set date column as index
    df.set_index('date', inplace=True)

    # Resample the DataFrame to 3-hour intervals and calculate mean
    df_resampled = df.resample('3h').mean()
    print(f'Data head(1) : {df_resampled.head(1)}')
    return df_resampled



def save_to_db(df, db_name, conn=conn, cursor=cursor):
    # dataframe to save
    print(40*'_')
    print()
    df = df.copy()
    print(f'Saving to database {db_name}...')
    
    if db_name == "averages":
        df.to_sql(name=db_name, # Name of SQL Table
            con=conn, # sqlite3.Connection
            if_exists='replace',  # drop the table before inserting new values. Means that i get all the data at all times
            )
    else:
        df.to_sql(name=db_name, # Name of SQL Table
                con=conn, # sqlite3.Connection
                if_exists='replace',
                index=True, # DF index is date_time
                index_label="date_time"  
                )
        
    conn.commit()
    return f'Data saved to database {db_name}'


def test_db():
    rows = cursor.execute("SELECT * FROM weather LIMIT 5").fetchall()

    return rows


def refresh_database():
    '''
    This function gets the current date, prepares the params, 
    get's back a df from another function get_data (which makes an API call to openweather)
    and then calls another function save_to_db which persists the data.
    The data here are the true labels. It also stores data up until last year in a training database.
    The refresh should happen once on start of the application. 
    '''
    print(40*'_')
    print()
    print("Refreshing database...")
    date = datetime.now()
    
    params = commun.weather_params

    # date to only date (without time)
    date_only = date.date()
    params["end_date"] = str(date_only)
    
    df = get_data(commun.weather_url, params, ["temperature_2m"])
    
    # Saving all the data
    message = save_to_db(df, "weather")

    # Filter data up to end 2023 for training    
    desired_date = datetime(2023, 12, 31).date()
    df_training = df[df.index.date <= desired_date]

    message_training = save_to_db(df_training, "training")
    
    print(f'message: {message}')
    print(f'message_training: {message_training}')
    
    return f'Database weather refreshed with data up until {date_only} and training data stored up until 31/12/2023'


def retrieve_training_data(conn,cursor):
    print(40*'_')
    print()
    print(f'Retrieving training data...')
    # Query to retrieve all data from the training database
    query = "SELECT * FROM training"
    
    # Execute the query
    cursor.execute(query)
    
    # Fetch all rows from the query result
    rows = cursor.fetchall()
    
    # Convert the rows to a DataFrame
    columns = [desc[0] for desc in cursor.description]
    df_training = pd.DataFrame(rows, columns=columns)
    
    return df_training


def retrieve_true_labels_for_date(date):
    print(40*'_')
    print()
    print("Retrieving True Labels...")
    day = date.day
    month = date.month
    year = date.year
    
    query = f"SELECT * FROM weather WHERE strftime('%d', date_time) = ? AND strftime('%m', date_time) = ? AND strftime('%Y', date_time) = ?"
    
    # Execute the query with the parameters
    cursor.execute(query, (day, month, year))
    
    # Fetch the results
    true_labels = cursor.fetchall()
    print(f"true labels: {true_labels}")
    return true_labels

def save_predictions(date_time_array, predictions, true_labels, model_name):
    # in db predictions
    print(40*'_')
    print()
    print("Saving predictions...")
    try:
        # Create a table to store predictions if it doesn't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS predictions (
                            id INTEGER PRIMARY KEY,
                            input_date DATETIME,
                            model_name TEXT,
                            prediction REAL,
                            true_label REAL
                          )''')
        
        # Insert predictions and true labels into the database
        for date_time, pred, true_label in zip(date_time_array, predictions, true_labels):
            cursor.execute('''INSERT INTO predictions (input_date, model_name, prediction, true_label)
                              VALUES (?, ?, ?)''', (date_time, model_name, pred, true_label))
                
        conn.commit()
        return "Predictions saved successfully"
    except Exception as e:
        return f'error: {e}'
    

def get_training_averages_from_db(av_names):
    print()
    print("Get training averages from db...")
    all_averages = []
    
    for av in av_names : 
        query = f"SELECT * FROM {av}"
    
        # Execute the query
        cursor.execute(query)
        
        # Fetch all rows from the query result
        rows = cursor.fetchall()
        
        # Convert the rows to a DataFrame
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
        all_averages.append(df)
    
    return all_averages
    
    
def get_training_data_for_date_minus_one_year(date):
    # Calculate the date one year ago
    year = date.year - 1
    month = date.month
    day = date.day
    
    if year < 2020 or year > 2023: # Training data period
        return False

    # INFO: # Not taking into account leap years
    # if month == 2 and day == 29 and not is_leap_year(year):
    #     day = 28
    
    one_year_ago = datetime(year, month, day)

    # Convert date to strings in the format 'YYYY-MM-DD'
    one_year_ago_str = one_year_ago.strftime('%Y-%m-%d')

    # Construct and execute the SQL query to retrieve training data for the specified date minus one year
    query = f"""
            SELECT *
            FROM your_training_table
            WHERE date_time == '{one_year_ago_str}' 
            """

    cursor.execute(query)
    training_data = cursor.fetchall()

    # Convert the retrieved data into a DataFrame
    columns = [desc[0] for desc in cursor.description]
    training_data_df = pd.DataFrame(training_data)
    
    print(f'training_data_df {training_data_df}')
    return training_data_df
    
