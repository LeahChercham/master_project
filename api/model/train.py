import mlflow
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from api.data.db_functions import retrieve_training_data

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


def get_mean_by_cat(data, cat_feature, value_feature):
    ''' Function that returns a dictionary where:
    the keys correspond to unique values of `cat_feature`, and
    the values correspond to average values of `real_feature`.'''
    return dict(data.groupby(cat_feature)[value_feature].mean())


def create_year_lags(df):
    # getting the temperature from a year ago
    lag_distance_year = int(365*24/3 )
    df[f'year_lag_{lag_distance_year}'] = df["temperature_2m"].shift(lag_distance_year)
    df.dropna(inplace=True)
    return df


def preprocessing(df, training=True):
    '''Full preprocessing function, for training and prediction data. Calculating lags and means.'''
    print(40*'_')
    print()
    print(f'Preprocessing data ...')
    data = pd.DataFrame(df.copy())
    # Set date column as index
    data.set_index('date_time', inplace=True)
    data.index = pd.to_datetime(data.index) 
    
    data = create_year_lags(data)
    data["month"] = data.index.month
    data["year"] = data.index.year
    data = get_time(data)
    data = get_season(data)
    
    # calculate average values only on train data to avoid data leak
    data["month_average"] = list(map(get_mean_by_cat(data, "month", "temperature_2m").get, data.month))
    data["year_average"] = list(map(get_mean_by_cat(data, "year", "temperature_2m").get, data.year))
    data["season_average"] = list(map(get_mean_by_cat(data, "season", "temperature_2m").get, data.season))
    data["time_of_day_average"] = list(map(get_mean_by_cat(data, "time_of_day", "temperature_2m").get, data.time_of_day))

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

    return X, y
    


def prepare_training_data(conn,cursor):
    '''Getting the training data from the training db and preprocessing it'''
    # get the data 
    data = retrieve_training_data(conn,cursor)
    
    # pre process it 
    X, y = preprocessing(data, True)
    
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