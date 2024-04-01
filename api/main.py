"""
Ce script doit contenir l'implémentation des endpoints pour les fonctionnalités suivantes :
- Génération des prédictions pour une date donnée,
- Récupération des prédictions pour une date donnée,
- Récupération des prédictions combinées avec des données réelles observées pour une période donnée
"""
from fastapi import FastAPI, HTTPException
from typing import Optional, List
import pandas as pd

# Import functions for data retrieval, model training, and prediction generation
from data import fetch_data, refresh_database
from train import train_model
from predict import generate_predictions, get_combined_data

app = FastAPI()

# Define endpoint for generating predictions for a specific date
@app.get("/predict/{date}/")
async def predict(date: str):
    try:
        # Download missing data and update database
        refresh_database()
        
        # Train the model using historical data up to a predefined duration before the prediction date
        train_model()
        
        # Generate predictions for the specified date using the trained model
        predictions = generate_predictions(date)
        
        return {"predictions": predictions}
    
    except Exception as e:
        # Return error message if any exception occurs
        raise HTTPException(status_code=500, detail=str(e))

# Define endpoint for retrieving predictions for a specific date
@app.get("/predictions/{date}/")
async def get_predictions(date: str):
    try:
        # Retrieve predictions for the specified date
        predictions = generate_predictions(date)
        
        return {"predictions": predictions}
    
    except Exception as e:
        # Return error message if any exception occurs
        raise HTTPException(status_code=500, detail=str(e))

# Define endpoint for retrieving predictions combined with observed data for a specific period
@app.get("/combined_predictions/")
async def get_combined_predictions(start_date: str, end_date: str):
    try:
        # Retrieve combined predictions and observed data for the specified period
        combined_data = get_combined_data(start_date, end_date)
        
        return {"combined_data": combined_data}
    
    except Exception as e:
        # Return error message if any exception occurs
        raise HTTPException(status_code=500, detail=str(e))

# Define a basic health check endpoint
@app.get("/healthcheck/")
async def healthcheck():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
