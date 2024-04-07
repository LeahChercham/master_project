# BIHAR MASTER II PROJET FINAL
This project is the final project for master II BIHAR Big Data and AI at Estia (bidart).  

The project is composed of three sub projects:
- Image classification
- Text classification
- Time series predictions
  
The notebooks for these subprojects can be found in the folder notebooks.
This readme concerns the Time Series predictions application, as we created an api for this. 

# Description

The time series predictions application has for goal to predict the temperature at a specific location, in this case Strasbourg, France. The data used for this project is the historical weather data from Open meteo. The data is stored in a sqlite database during runtime, at the end of the application, the db is resetted. The application is built using FastAPI and the predictions are made using a linear regression model.

## Main technologies used and for which purpose

FastAPI serves the endpoints of the API and feeds the params to the linear regression model.  
The script is written in python.  
Uvicorn is used to serve the API.  
The data is stored in a sqlite database.  
We use sklearn for the linear regression.

## Data flow & architecture

On start of the application, the database is refreshed with training data from 2020-01-01 to 2023-12-31 in the table training. We also refresh the table weather with the data up until today-1. The table weather contains basically our true labels.  
Then we preprocess the training data and fit the model, if it not already exists. Then we save it with pickle.    
There is an execution happening in order to show that everything is working as expected, preprocessing, predicting and creating a plot to compare predictions and true labels.  
Finally we start the FastAPI and serve the endpoints. 
  
A request to an prediction endpoint will trigger the preprocessing of the request date or date range, then it will feed the data to the trained model and make predictions. The predictions are then returned to the user.    

All the code is in the folder ./api. In data/db_functions we will find all the related database actions, in model/train we will find the preprocessing steps and the training of the model, in model/predict we will find all the functions related to the predictions and in main we will find the FastAPI code. We also have a commun file which gets some variables from our conig.ini file. Finally we have the monitoring folder in which we have a script creating a plot to compare predicted and true labels and the saved images.  

In the root of the repository you can find also the Dockerfile used to create a docker image, the requirements.txt file, the logs in api.log and in .github/workflows/cicd you can find the github actions workflow.  

## Comments
- The plot is not automatically created with each prediction

# Endpoints
## Documentation

Expected were four endpoints: generate prediction for a specific date, get predictions for a specific date, get predictions and true labels for a date range, get version of software and data

## Logging
The logging is done regularly

# Running the App 
Instructions to install dependencies, run the app, build the docker image, test the api.

## Running the app using a Venv

Git clone the repo then navigate to the project root and execute the following commands: 

```bash
python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

python .\api\main.py

```

Then go to http://127.0.0.1:8001/, there you can test the routes get/predictions/{date}, get/combined_predictions/{start_date}/{end_date} andget/version.  

Dates must be in this format YYYY-MM-DD  

You can also test the api using the test file. Execute the main as shown before, then open a second terminal, start the same venv and execute: 

```bash
python ./api/tests/test_api.py
```

## Using the docker image 

### Connect and pull
Connect to ghrc.io and pull the docker image.  

```bash
docker login ghcr.io -u <username> -p <access_token>
docker pull ghcr.io/leahchercham/master_project:a8f7ed6
```
### Execute API tests
Then you can execute the tests : (Scroll to the top of the output to see the test results):  
```bash
docker run --rm -p 8001:8001 ghcr.io/leahchercham/master_project:a8f7ed6 python ./api/tests/test_api.py
```
### Execute API
Or you can simply run the docker image and then use the FastAPI endpoint on your localhost:  
```bash
docker run --rm -p 8001:8001 ghcr.io/leahchercham/master_project:a8f7ed6
```


# CI/CD 

## Build docker image locally
This explains how to build the image locally. We will see later how we build it using github actions.  

- Navigate to project root   
- Execute following command:  

```bash
docker build -t image .
docker run -p 8001:8001 image
``` 

## CICD Steps
This part contains a short description of each step with their outputs (if any) . The file is cicd.yml.

The workflow CICD is executed when there is a push on the branch master.  
We have three jobs: versioning, build-test-image and push-image  

### versioning
This job is used to create a version and an imageName as outputs. The version is not used afterwards. I wanted to implement the tag :latest but wasn't able to.  

### build-test-image
This job is executing the API tests. It is building the docker image and then running the tests.  
IT needs versioning to be executed to work. Then we login to ghcr.io, build the image with the build-push-action but don't push the image just yet.
   
Then  we run the image and once it is running we run the api test script.  

### push-image
This job is pushing the image to ghcr.io. We use the docker build and push action and use the image Name defined in versioning. This is only executed after versioning and build-test-image.









# TODOs
- add other projects notebooks to this github
- add models to sqlite database
- write fastapi code
- dockerfile: démarrer et servir les endpoints de l'API / les couches sont optimisées pour ne pas réinstaller les dépendances lorsque le code change / La documentation sur la facon de générer l'image et l'architecture est fournie
- logging dans fichier
- tests automatisés des endpoints de l'API
- pipeline basé sur GH actions qui créé une image, lenvoie vers ghcr.io et exécute des tests de l'API

# Last working on: 
In /api: **main**, commun and train (do the functions of main next)