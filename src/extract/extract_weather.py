import json 
import time 
from datetime import date
from pathlib import Path

import requests

from src.extract.extract_cities import load_cities 

from src.utils.config import (BRONZE_DIR,DAILY_VARIABLES,FORECAST_DAYS,MAX_RETRIES,OPEN_METEO_URL,REQUEST_TIMEOUT,RETRY_BACKOFF_SECONDS,)
from src.utils.logger import get_Logger

logger = get_Logger(__name__)

def fetch_weather_for_city(city_name: str, lat: float, lng: float) -> dict | None:
        
        params = {
            "latitude": lat,
            "longitude": lng,
            "daily": ",".join(DAILY_VARIABLES),
            "forecast_days": FORECAST_DAYS,
            "timezone": "auto",
        }
        #pls tentaives 
        for attempt in range(1, MAX_RETRIES + 1):
                try:
                    response = requests.get(OPEN_METEO_URL, params=params, timeout=REQUEST_TIMEOUT)
                    # verification de code 
                    response.raise_for_status()  
                    return response.json()
        
                except requests.exceptions.Timeout:
                    logger.warning(f"[{city_name}] Timeout (tentative {attempt}/{MAX_RETRIES})")
        
                except requests.exceptions.HTTPError as e:
                    logger.warning(
                        f"[{city_name}] Erreur HTTP {response.status_code} "
                        f"(tentative {attempt}/{MAX_RETRIES}) : {e}"
                    )
                    # Un 4xx (ex: coordonnées invalides) ne se résoudra pas en réessayant
                    if 400 <= response.status_code < 500:
                        break
        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"[{city_name}] Erreur réseau (tentative {attempt}/{MAX_RETRIES}) : {e}")
        
                except ValueError:
                    # response.json() a échoué -> réponse non-JSON
                    logger.warning(f"[{city_name}] Réponse invalide, JSON non parsable (tentative {attempt})")
                #backoff
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)  
        
        logger.error(f"[{city_name}] Échec définitif après {MAX_RETRIES} tentatives")
        return None 
        
# orchestre toute l'extraction. 
def run_bronze_extraction() -> Path:
   
    cities = load_cities()

    run_date = date.today().isoformat()
    output_dir = BRONZE_DIR / run_date
    output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    failed_cities = []

    for _, row in cities.iterrows():
        city_name, lat, lng = row["city"], row["lat"], row["lng"]

        raw_data = fetch_weather_for_city(city_name, lat, lng)

        if raw_data is None:
            failed_cities.append(city_name)
            continue

        # 
        raw_data["_city_name"] = city_name
        raw_data["_extracted_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")

        safe_name = str(city_name).replace(" ", "_").replace("/", "_")
        output_path = output_dir / f"{safe_name}.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2)

        success_count += 1

    logger.info(f"Extraction terminée : {success_count} villes OK, {len(failed_cities)} échecs")
    if failed_cities:
        logger.warning(f"Villes en échec : {failed_cities}")

    # Petit manifest utile pour Silver et pour le monitoring
    manifest = {
        "run_date": run_date,
        "total_cities": len(cities),
        "success_count": success_count,
        "failed_cities": failed_cities,
    }
    with open(output_dir / "_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return output_dir

if __name__ == "__main__":
    run_bronze_extraction()
