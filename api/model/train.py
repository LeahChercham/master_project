import mlflow
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from api.data.db_functions import retrieve_training_data, save_to_db, get_training_averages_from_db, get_training_data_for_date_minus_one_year

import commun 
# Preprocessing functions

def get_season(df):
    '''Getting the seasons in order to calculate means per season later'''
    date_series = df.index
    seasons = {
        'spring': pd.date_range(start='2018-03-21', end='2018-06-20'),
        'summer': pd.date_range(start='2018-06-21', end='2018-09-22'),
        'autumn': pd.date_range(start='2018-09-23', end='2018-12-20')
    }

    season_series = pd.Series(index=date_series, dtype='object')
    #season_series = date_series
    for season, season_dates in seasons.items():
        season_series[date_series.strftime('%m-%d').isin(season_dates.strftime('%m-%d'))] = season

    season_series.fillna('winter', inplace=True)
    df['season'] = season_series

    return df


def get_time_of_day(hour):
    '''Getting the time of day in order to calculate means per moment later'''
    times = {
        'morning': [6, 9],
        'day': [12, 15],
        'evening': [18, 21],
        'night': [00, 3]
    }

    for time, hour_range in times.items():
        if hour in hour_range:
            return time
    return None

def get_time(df):
    date_series = df.index
    time_series = pd.Series(index=date_series, dtype='object')

    for hour in date_series.hour:
        time_of_day = get_time_of_day(hour)
        time_series[date_series.hour == hour] = time_of_day

    time_series.fillna('night', inplace=True)
    df['time_of_day'] = time_series

    return df



def create_year_lags(df, training = True):
    lag_distance_year = int(365*24/3 )
    
    if training:
        # getting the temperature from a year ago
        df[f'year_lag_{lag_distance_year}'] = df["temperature_2m"].shift(lag_distance_year)
        df.dropna(inplace=True)
    else:
        # Retrieve training data for the date minus one year
        training_data = get_training_data_for_date_minus_one_year(df.index[0])
        df[f'year_lag_{lag_distance_year}'] = training_data[f'year_lag_{lag_distance_year}'].values

    print(f'lags: {df[f'year_lag_{lag_distance_year}']}')
    
    return df


def preprocessing(df, training=True, conn=None, cursor=None):
    '''Full preprocessing function, for training and prediction data. Calculating lags and means.'''
    print(40*'_')
    print()
    print(f'Preprocessing data ...')
    data = pd.DataFrame(df.copy())
    # Set date column as index
    data.set_index('date_time', inplace=True)
    data.index = pd.to_datetime(data.index) 
    
    data = create_year_lags(data, training)
    
    
    data["month"] = data.index.month
    data["year"] = data.index.year
    data = get_time(data)
    data = get_season(data)
    
    av_names = ['averages_month', 'averages_year', 'averages_season', 'averages_time_of_day', 'averages_years_average']
    
    if training:
        averages = {}
        
        # calculate average values only on train data to avoid data leak
        averages["month"] = data.groupby("month")["temperature_2m"].mean()
        averages["year"] = data.groupby("year")["temperature_2m"].mean()
        averages["season"] = data.groupby("season")["temperature_2m"].mean()
        averages["time_of_day"] = data.groupby("time_of_day")["temperature_2m"].mean()
        averages["years_average"] = averages["year"].mean()

        averages_year = pd.DataFrame.from_dict({"temperature_2m":averages["year"]})
        averages_month = pd.DataFrame.from_dict({"temperature_2m": averages["month"]})
        averages_season = pd.DataFrame.from_dict({"temperature_2m":averages["season"]})
        averages_time_of_day = pd.DataFrame.from_dict({"temperature_2m":averages["time_of_day"]})
        averages_years_average = pd.DataFrame.from_dict({"temperature_2m": averages["years_average"]}, orient='index', columns=["years_average"])
        averages_years_average.index.name = "years_average"

        
        all_averages = [averages_month, averages_year, averages_season, averages_time_of_day, averages_years_average]

        # Save each average to the database
        for av, av_name in zip(all_averages, av_names):
            save_to_db(av, av_name, conn, cursor)

    else:
        # Load averages from database
        all_averages = get_training_averages_from_db(av_names)
    
    print(50*"_")
    print(50*"HIER")
    print(50*"!")
    print(f'ALL averages PREDICTION {all_averages}')
    
    # Fill missing values with averages
    data["month_average"] = data["month"].map(averages["month"])
    data["year_average"] = data["year"].map(averages["year"])
    data["season_average"] = data["season"].map(averages["season"])
    data["time_of_day_average"] = data["time_of_day"].map(averages["time_of_day"])
    
    # Handle missing values for year average
    years_average_mean = data['year_average'].mean()
    data['year_average'].fillna(years_average_mean, inplace=True)
    

    # drop features used for calculating average values
    data.drop(columns=["month","year", "season", "time_of_day"], axis=1, inplace=True)

    if training:
        # Split data
        X = data.drop(["temperature_2m"], axis=1)
        y = data["temperature_2m"]
    else: 
        X = data
        y = None

    print(40*'*')
    print(f'preprocessed X: {X.head(1)} and y: {y.head(1)}')
    return X, y
    


def prepare_training_data(conn,cursor):
    '''Getting the training data from the training db and preprocessing it'''
    # get the data 
    data = retrieve_training_data(conn,cursor)
    
    # pre process it 
    X, y = preprocessing(data, True, conn, cursor)
    
    return X, y 




def fit_model(X_train, y_train):
    ''' This function is creating and fitting a linear regression model
    Model to create: linear_regression_X_train__lags_False__yearlag_True__aggregates_True__exo_False '''
    model_name = commun.model_name
    print(40*'_')
    print()
    print("Creating model ...")
    # Define and train the model
    lr = LinearRegression()
    
    print()
    print('Training model ...')
    lr.fit(X_train, y_train)
        
    with mlflow.start_run(run_name=model_name) as run:
        mlflow.log_param("model", model_name)
        mlflow.sklearn.log_model(sk_model=lr,  artifact_path="model")
    
    # Register the model using the run ID
    mlflow.register_model(f"models", model_name)

    print()
    print("Model saved to MLflow Registry")
    
    return lr