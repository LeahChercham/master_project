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

VERSION = str(config.get("SOFTWARE", "VERSION"))
sw_version = VERSION



