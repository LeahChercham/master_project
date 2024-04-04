import datetime
import mlflow.pyfunc
import pandas as pd
import numpy as np
import sys
import os
from sklearn.metrics import mean_squared_error
from data import retrieve_true_labels_for_date, save_predictions


from ..data.data import retrieve_true_labels_for_date, save_predictions


def generate_predictions(input_data):
    # load the model :
    model_name = "linear_regression_model"
    loaded_model = mlflow.pyfunc.load_model(model_name)
    
    # input_data is supposed to be a date: TODO verify
    print(f'input data: {input_data}')
    date_time_array = []
    
    # Set the start time to the specified date at 00:00
    start_time = datetime(input_data.year, input_data.month, input_data.day)
    
    # Generate datetime values with 3-hour intervals from 00:00 to 23:59
    current_time = start_time
    while current_time < start_time + datetime.timedelta(days=1):
        date_time_array.append(current_time)
        current_time += datetime.timedelta(hours=3)
    
    print(f'date_time_array {date_time_array}')
    
    # output a list of predictions (hours from 0 to 24 in 3h steps) TODO verify
    predictions = loaded_model.predict(date_time_array)
    
    print(f'predictions: {predictions}')
    
    # TODO get true labels TEST
    true_labels = retrieve_true_labels_for_date(input_data)
    
    # TODO: save predictions to db TEST
    save_predictions(predictions, true_labels, model_name)
    
    
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


