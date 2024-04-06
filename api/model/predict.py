from datetime import datetime
import mlflow.pyfunc
import pandas as pd
import numpy as np
import sys
import os
from sklearn.metrics import mean_squared_error
from api.model.train import preprocessing
import commun
import mlflow

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from api.data.db_functions import retrieve_all_from_db_name, retrieve_true_labels_for_date, save_to_db


def generate_predictions(input_data, conn, cursor):
    print(40*'_')
    print()
    print("Preparing Data for predictions ... ")
    
    logged_model = 'runs:/d023dbaf57af4cd3a6939de1c32c9695/model'

    # Load model as a PyFuncModel.
    loaded_model = mlflow.pyfunc.load_model(logged_model)
    input_data = str(input_data)
    date_object = datetime.fromisoformat(input_data)

    # Set the start time to the specified date at 00:00 (as we want 3 hour steps)
    start_time = datetime(date_object.year, date_object.month, date_object.day)
    end_time = datetime(date_object.year, date_object.month, date_object.day, 21, date_object.minute, date_object.second)

    
    
    # Generate datetime values with 3-hour intervals from 00:00 to 23:59
    date_time_array = []
    current_time = start_time
    while current_time <= end_time:
        date_time_array.append(current_time)
        # Add 3 hours to the current time
        if current_time.hour == 21 :
            break
        current_time = current_time.replace(hour=current_time.hour + 3)


    # preprocess data 
    df = pd.DataFrame({'date_time': date_time_array})
    preprocessed_df, y = preprocessing(df, False, conn, cursor)

    print(40*'_')
    print()
    print("Predicting ... ")
    # output a list of predictions (hours from 0 to 24 in 3h steps)
    predictions = loaded_model.predict(preprocessed_df) # Array of temperatures

    true_labels = retrieve_true_labels_for_date(date_object, conn, cursor) # Returns an array of tupples (date_time, temperature)

    # preprocessed_df is a dataframe with date_time as index and some columns. 
    # add to preprocessed_df a column predictions thanks to the array predictions (array containing the predictions in the correct order), add also a column true_labels thanks to true_labels (array of tuples (date_time, temperature) and add column model where it is commun.model_name for all 
    pred_true_preprocessed_df = preprocessed_df.copy()
    pred_true_preprocessed_df['model'] = commun.model_name
    
    predictions_series = pd.Series(predictions, index=pred_true_preprocessed_df.index, name='predictions')

    # Convert the datetime strings in true_labels to the same format
    
    true_labels_array = [x[1] for x in true_labels]
    true_labels_series = pd.Series(true_labels_array, index=pred_true_preprocessed_df.index, name='true_labels')

    pred_true_preprocessed_df = pd.concat([pred_true_preprocessed_df, predictions_series, true_labels_series], axis=1)

    # Save predictions to db
    save_to_db(pred_true_preprocessed_df, "predictions", conn, cursor)
    
    
    # TODO : save as run and calculate score

    return predictions_series





def get_combined_data(start_date, end_date):
    return "hello"


