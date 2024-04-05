from datetime import datetime
import mlflow.pyfunc
import pandas as pd
import numpy as np
import sys
import os
from sklearn.metrics import mean_squared_error
import commun
import mlflow

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from api.data.db_functions import retrieve_true_labels_for_date, save_predictions


def generate_predictions(input_data):
    print(40*'_')
    print()
    print("Generating predictions ... ")
    
    logged_model = 'runs:/d023dbaf57af4cd3a6939de1c32c9695/model'

    # Load model as a PyFuncModel.
    loaded_model = mlflow.pyfunc.load_model(logged_model)
    
    # input_data is supposed to be a date: TODO verify
    print(f'input data: {input_data}')
    date_object = datetime.fromisoformat(input_data)

    # Set the start time to the specified date at 00:00
    start_time = datetime(date_object.year, date_object.month, date_object.day)
    print(f"start time {start_time}")
    
    end_time = datetime(date_object.year, date_object.month, date_object.day, 21, date_object.minute, date_object.second)
    print(f'end_time: {end_time}')
    
    # Generate datetime values with 3-hour intervals from 00:00 to 23:59
    date_time_array = []
    current_time = start_time
    while current_time <= end_time:
        date_time_array.append(current_time)
        # Add 3 hours to the current time
        if current_time.hour == 21 :
            break
        current_time = current_time.replace(hour=current_time.hour + 3)

    
    print(f'date_time_array {date_time_array}')
    
    # preprocess data 
    # TODO preprocess the data we want to make predictions for
    # output a list of predictions (hours from 0 to 24 in 3h steps) TODO verify
    predictions = loaded_model.predict(date_time_array)
    
    print(f'predictions: {predictions}')
    
    # TODO get true labels TEST
    true_labels = retrieve_true_labels_for_date(input_data)
    
    # TODO: save predictions to db TEST
    save_predictions(predictions, true_labels, commun.model_name)
    
    
    # TODO: save predictions as run to mlflow and calculate score
    with mlflow.start_run():
        # log input data 
        mlflow.log_param("input_data", input_data)
        
        # log predictions
        mlflow.log_param("predictions", predictions)
        
        # log score
        rmse = mean_squared_error(true_labels, predictions, squared=True)
        mlflow.log_metric('rmse', rmse)


    return predictions





def get_combined_data(start_date, end_date):
    return "hello"


