"""
Ce script doit contenir l'implémentation des endpoints pour les fonctionnalités suivantes :
- Génération des prédictions pour une date donnée,
- Récupération des prédictions pour une date donnée,
- Récupération des prédictions combinées avec des données réelles observées pour une période donnée
"""
from fastapi import FastAPI, HTTPException
from typing import Optional, List
import pandas as pd
import uvicorn

# Import functions for data retrieval, model training, and prediction generation
from data.data import refresh_database, create_db_connection

from api.model.train import fit_model, prepare_training_data

from api.model.predict import generate_predictions, get_combined_data

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello world!"}

# Define endpoint for generating predictions for a specific date
@app.get("/predict/{date}/")
def predict(date: str):
    try:
        # Generate predictions for the specified date using the trained model
        predictions = generate_predictions(date)
        
        return {"predictions": predictions}

    
    except Exception as e:
        # Return error message if any exception occurs
        raise HTTPException(status_code=500, detail=str(e))

# Define endpoint for retrieving predictions for a specific date
@app.get("/predictions/{date}/")
def get_predictions(date: str):
    try:
        # Retrieve predictions for the specified date
        predictions = generate_predictions(date)
        
        return {"predictions": predictions}
    
    except Exception as e:
        # Return error message if any exception occurs
        raise HTTPException(status_code=500, detail=str(e)) # prepare exceptions TODO

# Define endpoint for retrieving predictions combined with observed data for a specific period
@app.get("/combined_predictions/")
def get_combined_predictions(start_date: str, end_date: str):
    try:
        # Retrieve combined predictions and observed data for the specified period
        combined_data = get_combined_data(start_date, end_date)
        
        return {"combined_data": combined_data}
    
    except Exception as e:
        # Return error message if any exception occurs
        raise HTTPException(status_code=500, detail=str(e))

# Define a basic health check endpoint
@app.get("/healthcheck/") #INFO: this works, TODO: might elaborate
def healthcheck():
    return {"status": "ok"}

if __name__ == "__main__":
    
    # Create database connection 
    conn, cursor = create_db_connection()
    
    # refresh database with data up to date and training da
    print(refresh_database())
    
    # use data until 12/2023 as training data and preprocess it
    X, y = prepare_training_data()
    
    # create and fit the model
    model = fit_model(X, y)
    
    # start Fast API
    uvicorn.run("main:app", port=8000, reload=True)
    
    # at the end, close connection  TODO
    # conn.close()
    
