from pathlib import Path
import os

# difinir les chemins (cas dans un autre project )

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"

# Chemin vers le CSV SimpleMaps telechrge manuellement

CITIES_CSV_PATH = DATA_DIR / "raw" / "ma.csv"

# API METEO 

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

DAILY_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "precipitation_probability_max",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "weather_code",
] 

# nombre de jours de prévision à récupérer
FORECAST_DAYS = 7     
# nombre de secondes 
REQUEST_TIMEOUT = 10    
# nombre de tentative 
MAX_RETRIES = 3
# multiplié par le numéro de tentative
RETRY_BACKOFF_SECONDS = 2  

# Postgres 

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "weather_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

SCHEMA_SQL_PATH = PROJECT_ROOT / "sql" / "schema.sql"


 