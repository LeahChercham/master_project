"""
Ce script doit contenir l'implémentation des endpoints pour les fonctionnalités suivantes :
- Génération des prédictions pour une date donnée,
- Récupération des prédictions pour une date donnée,
- Récupération des prédictions combinées avec des données réelles observées pour une période donnée
"""
from contextlib import asynccontextmanager
import sqlite3
from fastapi import FastAPI, HTTPException, Query
from datetime import date, datetime
from typing import Optional, List
from fastapi.responses import RedirectResponse
import pandas as pd
import uvicorn
from pydantic import BaseModel, Field

# Import functions for data retrieval, model training, and prediction generation
from data.db_functions import refresh_database, create_db_connection

from api.model.train import fit_model, prepare_training_data

from api.model.predict import generate_predictions, generate_period_predictions
from api.monitoring.monitoring import plot_true_pred

import logging
from commun import sw_version, weather_params

# Set up logging configuration
logging.basicConfig(filename='api.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
conn = sqlite3.connect('weather.db')
cursor = conn.cursor()


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     logging.info(f'Starting fast API')

#     # Create database connection 
#     conn, cursor = create_db_connection()
    
#     # refresh database with data up to date and training da
#     print(refresh_database(conn,cursor))
    
#     # use data until 12/2023 as training data and preprocess it
#     X, y = prepare_training_data(conn, cursor)
        
#     # create and fit the model
#     model = fit_model(X, y)
    
#     # #TESTS
#     # predictions, pred_true = generate_predictions("2024-05-02", conn, cursor)
#     # predictions, pred_true, true_labels_df = generate_period_predictions("2024-01-02", "2024-01-10", conn, cursor)
#     # print(f'path to image: {plot_true_pred(predictions, true_labels_df)}')
#     yield
#     logging.info("Ending fast API")

# app = FastAPI(lifespan=lifespan)
app = FastAPI()


class DataForm(BaseModel):
    selected_date: date = Field(description="Select a date")

@app.get("/") # TODO redirect to docs
def root():
    logging.info(f'Redirecting from "/" to "/docs"')
    # Redirect to the "/docs" endpoint
    return RedirectResponse(url="/docs")


# Define endpoint for retrieving predictions for a specific date
@app.get("/predictions/{date}/") # works
def get_predictions(date: date):
    logging.info(f'Received request for predictions for date: {date}')
    print(f'Received request for predictions for date: {date}')

    try:
        conn, cursor = create_db_connection()
        # Retrieve predictions for the specified date
        predictions, pred_true = generate_predictions(date, conn, cursor)
        logging.info(f'Returning predictions for date: {date}')
        return {"predictions and true labels if they are" : pred_true}
    
    except Exception as e:
        # Return error message if any exception occurs
        logging.error(f'Error occurred while processing prediction request for date {date}: {e}')
        raise HTTPException(status_code=500, detail=str(e))
    
# Define endpoint for retrieving predictions combined with observed data for a specific period
@app.get("/combined_predictions/{start_date}/{end_date}/")
def get_combined_predictions(start_date: date, end_date: date):
    print(f'start_date and end_date : {start_date} , {end_date}')
    logging.info(f'start_date and end_date : {start_date} , {end_date}')
    try:
        conn, cursor = create_db_connection()
        # Retrieve combined predictions and observed data for the specified period
        predictions, pred_true, true_labels_df = generate_period_predictions(start_date,end_date, conn, cursor)
        
        return {"predictions and true labels if they are": pred_true}
    
    except Exception as e:
        # Return error message if any exception occurs
        logging.error(f'Error occurred while processing combined_predictions for start_date {start_date} and end_date {end_date}: {e}')
        raise HTTPException(status_code=500, detail=str(e))


# Version endpoint
@app.get("/version/")
def version():
    try:
        logging.info(f'Version request received')

        return {"software_version": sw_version, 
                "data_version": weather_params}
        
    except Exception as e:
        logging.error(f"Error occurred while processing version request: {str(e)}")
        return {"error": "An error occurred while processing the request"}, 500
    
    
def run_uvicorn():
    print("Running uvicorn")
    uvicorn.run(app, port=8001, reload=False)

if __name__ == "__main__":
    # Create database connection 
    conn, cursor = create_db_connection()
    
    # refresh database with data up to date and training da
    print(refresh_database(conn,cursor))
    
    # use data until 12/2023 as training data and preprocess it
    X, y = prepare_training_data(conn, cursor)
        
    # create and fit the model
    model = fit_model(X, y)    
    

    run_uvicorn()
    # #TESTS
    # predictions, pred_true = generate_predictions("2024-05-02", conn, cursor)
    # predictions, pred_true, true_labels_df = generate_period_predictions("2024-01-02", "2024-01-10", conn, cursor)
    # print(f'path to image: {plot_true_pred(predictions, true_labels_df)}')
    # start Fast API
    # uvicorn.run(app, port=8001, reload=False)
