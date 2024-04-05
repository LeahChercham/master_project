from sklearn.preprocessing import MinMaxScaler
import pickle
import os

# Using INI configuration file
from configparser import ConfigParser

# project root
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(ROOT_DIR, 'config.ini')

config = ConfigParser()
config.read(CONFIG_PATH)
LATITUDE = float(config.get("WEATHER_PARAMS", "LATITUDE"))
LONGITUDE = float(config.get("WEATHER_PARAMS", "LONGITUDE"))
START_DATE = str(config.get("WEATHER_PARAMS", "START_DATE"))
END_DATE = str(config.get("WEATHER_PARAMS", "END_DATE"))
HOURLY = str(config.get("WEATHER_PARAMS", "HOURLY"))
TIMEZONE = str(config.get("WEATHER_PARAMS", "TIMEZONE"))
WEATHER_URL = str(config.get("WEATHER_PARAMS", "WEATHER_URL"))

weather_params = {
    "latitude": LATITUDE,
	"longitude": LONGITUDE,
	"start_date": START_DATE,
	"end_date": END_DATE,
	"hourly": HOURLY,
	"timezone": TIMEZONE
}    

MODEL_NAME = str(config.get("MODEL", "MODEL_NAME"))
model_name = MODEL_NAME

weather_url = WEATHER_URL

def preprocess_data(X):
    print(40*"_")
    print("Preprocessing data...")
    
    res = X.copy()
    
    res = scaling_dew(res)
    
    # res = # TODO: finish this function
    
    
    
    print("Preprocessing done...")
    print(40*"_")
    return res


def preprocess_dew_(X):
    res = X.copy()

    # Apply MinMaxScaler to the 'dew_point_2m' column
    scaler = MinMaxScaler(feature_range=(0, 1))
    res['dew_point_2m_normalized'] = scaler.fit_transform(res[['dew_point_2m']])
    res = res.drop(columns=['dew_point_2m'])

    return res


def separate_xy(df, target_column):
    # Split the data into features and target
    X = df.index
    y = df[[target_column]]

    return X, y

def separate_endogene_from_exogene(df, exogene_columns):
    
    # example usage
    # exogene_columns = ['dew_point_2m_normalized']  
    # exog_val = X_val_dew[exogene_columns]
    # endog_val = X_val_dew.drop(columns=exogene_columns)
    
    # Separate the exogenous variables from the endogenous time series data
    exogene_df = df[exogene_columns]

    # Remove the exogenous columns from the endogenous time series data
    endogene_df = df.drop(columns=exogene_columns)

    return endogene_df, exogene_df



def split_data_time(X, y, train_size=0.7, val_size=0.15, day=None):
    if day == None:
        # Calculate the lengths for training and validation sets
        len_train = int(len(X) * train_size)
        len_val = int(len(X) * val_size)

        # Calculate the indices for splitting
        ind_train_end = len_train
        ind_val_end = ind_train_end + len_val

        # Split the data into training, validation, and test sets
        X_train = X[:ind_train_end]
        X_val = X[ind_train_end:ind_val_end]
        X_test = X[ind_val_end:]

        # Split the labels accordingly
        y_train = y[:ind_train_end]
        y_val = y[ind_train_end:ind_val_end]
        y_test = y[ind_val_end:]

        return X_train, X_val, X_test, y_train, y_val, y_test
    
    else:
        # Find the index corresponding to the start of the specific day (00:00 timestamp) #TODO: verify if this works
        day_index = X.index[X.index.date == day.date()][0]

        # Split the data into training and test sets based on the specific date
        X_train = X[:day_index]
        X_test = X[day_index:]

        # Split the labels accordingly
        y_train = y[:day_index]
        y_test = y[day_index:]

        # No validation set for this case
        X_val, y_val = None, None
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
