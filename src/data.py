import pandas as pd
import requests

# c'est pour le fichier csv 

df = pd.read_csv("ma.csv")
print(df.columns.tolist())
print(df.shape)
print("\n\n",df.head(10))

# c'est pour api 

url = "https://api.open-meteo.com/v1/forecast"

pparams = {
    "latitude": 31.63,
    "longitude": -8.00,
    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,"
             "precipitation_probability_max,wind_speed_10m_max,"
             "wind_gusts_10m_max,weather_code",
    "timezone": "auto"
}

donnees = requests.get(url,params=pparams,timeout=10)
print(donnees.status_code)
response = donnees.json()
print(response)