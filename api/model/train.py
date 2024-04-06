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



def create_year_lags(df, training = True, conn=None, cursor=None, date_range=None):
    lag_distance_year = int(365*24/3 )
    
    if training:
        # getting the temperature from a year ago
        df[f'year_lag_{lag_distance_year}'] = df["temperature_2m"].shift(lag_distance_year)
        df.dropna(inplace=True)
    elif date_range:
        training_data = []
        for date in date_range:
            # Retrieve training data for the specified date minus one year
            td = get_training_data_for_date_minus_one_year(date, conn, cursor)
            training_data.append(td)
            
        # Concatenate the list of DataFrames along the rows
        training_data = pd.concat(training_data, ignore_index=True)
        
        # Set the 'date_time' column as the index
        training_data.set_index('date_time', inplace=True)
        
        # Assign the temperature values to the corresponding column in df
        df[f'year_lag_{lag_distance_year}'] = training_data[f'temperature_2m'].values
    else:
        # Retrieve training data for the date minus one year
        training_data = get_training_data_for_date_minus_one_year(df.index[0], conn, cursor)
        df[f'year_lag_{lag_distance_year}'] = training_data[f'temperature_2m'].values
    
    return df



# Define functions to map values from averages dictionaries
def map_month_average(month, averages):
    return averages.get(str(month))

def map_year_average(year, averages):
    return averages.get(str(year))

def map_season_average(season, averages):
    return averages.get(season)

def map_time_of_day_average(time_of_day, averages):
    return averages.get(time_of_day)




def preprocessing(df, training=True, conn=None, cursor=None, period=False, date_range=None):
    '''Full preprocessing function, for training and prediction data. Calculating lags and means.'''
    print(40*'_')
    print()
    print(f'Preprocessing data ...')
    data = pd.DataFrame(df.copy())
    # Set date column as index
    data.set_index('date_time', inplace=True)
    data.index = pd.to_datetime(data.index) 
    
    if period:
        data = create_year_lags(data, training, conn, cursor, date_range=date_range)
    else:
        data = create_year_lags(data, training, conn, cursor)
    
    
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
        averages_years_average = pd.DataFrame.from_dict({"temperature_2m": averages["years_average"]}, orient='index', columns=["temperature_2m"])
        averages_years_average.index.name = "years_average"


        
        all_averages_array = [averages_month, averages_year, averages_season, averages_time_of_day, averages_years_average]
        
        all_averages = {}
        
        # Save each average to the database
        for av, av_name in zip(all_averages_array, av_names):
            save_to_db(av, av_name, conn, cursor)
            all_averages[av_name] = av.to_dict()
            

    else:
        # Load averages from database
        all_averages = get_training_averages_from_db(av_names, conn, cursor)
    
    
    if training:
        # Apply mapping functions to create new columns
        data["month_average"] = data["month"].apply(lambda x: all_averages["averages_month"]["temperature_2m"].get(x))
        data["year_average"] = data["year"].apply(lambda x: all_averages["averages_year"]["temperature_2m"].get(x))
        data["season_average"] = data["season"].apply(lambda x: all_averages["averages_season"]["temperature_2m"].get(x))
        data["time_of_day_average"] = data["time_of_day"].apply(lambda x: all_averages["averages_time_of_day"]["temperature_2m"].get(x))
            # Handle missing values for year average
        years_average_mean = data['year_average'].mean()
        data['year_average'].fillna(years_average_mean, inplace=True)   

    else: # dictionnary for prediction is slightly different
        data["month_average"] = data["month"].apply(lambda x: all_averages["averages_month"]["temperature_2m"][list(all_averages["averages_month"]["date_time"].values()).index(x)])
        data["year_average"] = all_averages["averages_years_average"]["temperature_2m"][0]
        data["season_average"] = data["season"].apply(lambda x: all_averages["averages_season"]["temperature_2m"][list(all_averages["averages_season"]["date_time"].values()).index(x)])
        data["time_of_day_average"] = data["time_of_day"].apply(lambda x: all_averages["averages_time_of_day"]["temperature_2m"][list(all_averages["averages_time_of_day"]["date_time"].values()).index(x)])

    
    # drop features used for calculating average values
    data.drop(columns=["month","year", "season", "time_of_day"], axis=1, inplace=True)
    data.reset_index(inplace=True)

    if training:
        # Split data
        X = data.drop(["temperature_2m"], axis=1)
        y = data["temperature_2m"]
        X.set_index('date_time', inplace=True)

    else: 
        X = data
        y = None
        X.set_index('date_time', inplace=True)
        
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