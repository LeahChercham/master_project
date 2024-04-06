# BIHAR MASTER II PROJET FINAL
## Description
This project is the final project for master II BIHAR Big Data and AI at Estia (bidart).  

The project is composed of three sub projects:
- Image classification
- Text classification
- Time series predictions


High-level description

Data flow & architecture

Main technologies used and for which purpose

# Running locally
Instructions to install dependencies, run, build, test

## Using a Venv
```bash
python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

```

## Running the application locally
- Navigate to project root
- Execute following command:

```bash

python .\api\data\data.py

```


# CI/CD steps

## Build docker image 
- Navigate to project root
- Execute following command:
```bash
docker build -t image
docker run -p 8001:8001 image
``` 

Short description of each step with their outputs (if any)

See example here: https://github.com/estia-bihar/correction

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