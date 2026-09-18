# Nettoyage et structuration des données Bronze.
import json
from datetime import date
from pathlib import Path

import pandas as pd

from src.extract.extract_cities import load_cities
from src.utils.config import BRONZE_DIR, SILVER_DIR
from src.utils.logger import get_Logger

logger = get_Logger(__name__)
# data quality checks 
TEMP_MIN_PLAUSIBLE = -20.0
TEMP_MAX_PLAUSIBLE = 60.0
PRECIP_MAX_PLAUSIBLE = 500.0   
WIND_MAX_PLAUSIBLE = 300.0     

def read_bronze_files(run_date: str | None = None) -> pd.DataFrame:
   
    run_date = run_date or date.today().isoformat()
    bronze_path = BRONZE_DIR / run_date

    if not bronze_path.exists():
        raise FileNotFoundError(f"Dossier bronze introuvable : {bronze_path}")

    frames = []
    for json_file in sorted(bronze_path.glob("*.json")):
        # ignore _manifest.json
        if json_file.name.startswith("_"):   
            continue

        try:
            with open(json_file, encoding="utf-8") as f:
                payload = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Fichier illisible ignoré : {json_file.name} ({e})")
            continue

        if "daily" not in payload:
            logger.warning(f"Pas de section 'daily' dans {json_file.name}, ignoré")
            continue

        df = pd.DataFrame(payload["daily"])
        # Oajouter ces infos fi dataframe 
        df["city"] = payload.get("_city_name")
        df["latitude"] = payload.get("latitude")
        df["longitude"] = payload.get("longitude")
        df["extracted_at"] = payload.get("_extracted_at")
        frames.append(df)

    if not frames:
        raise ValueError(f"Aucun fichier exploitable dans {bronze_path}")
    # 120 × 7 = 840
    raw = pd.concat(frames, ignore_index=True)
    logger.info(f"{len(frames)} fichiers lus -> {len(raw)} lignes brutes")
    return raw

#  Standardisation types

def standardize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={
        "time": "forecast_date",
        "temperature_2m_max": "temp_max",
        "temperature_2m_min": "temp_min",
        "precipitation_sum": "precipitation_mm",
        "precipitation_probability_max": "precipitation_prob",
        "wind_speed_10m_max": "wind_speed_max",
        "wind_gusts_10m_max": "wind_gust_max",
        "weather_code": "weather_code",
    })
    # coerce -> not a time
    df["forecast_date"] = pd.to_datetime(df["forecast_date"], errors="coerce").dt.date
    df["extracted_at"] = pd.to_datetime(df["extracted_at"], errors="coerce")
    df["city"] = df["city"].astype("string").str.strip()

    numeric_cols = [
        "temp_max", "temp_min", "precipitation_mm", "precipitation_prob",
        "wind_speed_max", "wind_gust_max", "latitude", "longitude",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["weather_code"] = pd.to_numeric(df["weather_code"], errors="coerce").astype("Int64")

    logger.info("Types standardisés")
    return df

# supprimer doublans  

def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
  
    before = len(df)
    df = (df.sort_values("extracted_at")
            .drop_duplicates(subset=["city", "forecast_date"], keep="last")
            .reset_index(drop=True))
    removed = before - len(df)
    if removed:
        logger.warning(f"{removed} doublons (city, forecast_date) supprimés")
    else:
        logger.info("Aucun doublon détecté")
    return df


def handle_inconsistencies(df: pd.DataFrame) -> pd.DataFrame:
   
    # temp_min > temp_max
    swapped = df["temp_min"] > df["temp_max"]
    if swapped.any():
        logger.warning(f"{swapped.sum()} lignes avec temp_min > temp_max -> mises à NaN")
        df.loc[swapped, ["temp_min", "temp_max"]] = pd.NA

    # range validation 
    for col in ["temp_max", "temp_min"]:
        out = (df[col] < TEMP_MIN_PLAUSIBLE) | (df[col] > TEMP_MAX_PLAUSIBLE)
        if out.any():
            logger.warning(f"{out.sum()} valeurs aberrantes dans {col} -> NaN")
            df.loc[out, col] = pd.NA

    # precipitation negative 

    neg_precip = df["precipitation_mm"] < 0
    if neg_precip.any():
        logger.warning(f"{neg_precip.sum()} précipitations négatives -> NaN")
        df.loc[neg_precip, "precipitation_mm"] = pd.NA

    too_much_rain = df["precipitation_mm"] > PRECIP_MAX_PLAUSIBLE
    if too_much_rain.any():
        logger.warning(f"{too_much_rain.sum()} précipitations aberrantes -> NaN")
        df.loc[too_much_rain, "precipitation_mm"] = pd.NA

    for col in ["wind_speed_max", "wind_gust_max"]:
        bad_wind = (df[col] < 0) | (df[col] > WIND_MAX_PLAUSIBLE)
        if bad_wind.any():
            logger.warning(f"{bad_wind.sum()} valeurs de vent aberrantes dans {col} -> NaN")
            df.loc[bad_wind, col] = pd.NA

    # Probabilité de précipitation : doit rester dans [0, 100]
    bad_prob = (df["precipitation_prob"] < 0) | (df["precipitation_prob"] > 100)
    if bad_prob.any():
        logger.warning(f"{bad_prob.sum()} probabilités hors [0,100] -> NaN")
        df.loc[bad_prob, "precipitation_prob"] = pd.NA

    return df

# Jointure les cities 

def join_cities(df: pd.DataFrame) -> pd.DataFrame:
    
    try:
        cities = load_cities()
    except FileNotFoundError:
        logger.warning("Référentiel villes indisponible, jointure ignorée")
        return df

    cities = cities.rename(columns={"lat": "city_lat", "lng": "city_lng"})
    cities["city"] = cities["city"].astype("string").str.strip()
    cities = cities.drop_duplicates(subset=["city"], keep="first")

    merged = df.merge(cities, on="city", how="left")
    # pas de ville 
    unmatched = merged["city_lat"].isna().sum()
    if unmatched:
        logger.warning(f"{unmatched} lignes sans correspondance dans le référentiel villes")
    logger.info(f"Jointure villes effectuée : {len(merged)} lignes")
    return merged

# rapport qualité
def quality_report(df: pd.DataFrame) -> dict:
    report = {
        "rows": len(df),
        "cities": int(df["city"].nunique()),
        "date_min": str(df["forecast_date"].min()),
        "date_max": str(df["forecast_date"].max()),
        "missing_values": {
            col: int(df[col].isna().sum())
            for col in ["temp_max", "temp_min", "precipitation_mm",
                        "precipitation_prob", "wind_speed_max", "wind_gust_max"]
        },
    }

    logger.info(
        f"QUALITÉ | {report['rows']} lignes | {report['cities']} villes | "
        f"période {report['date_min']} -> {report['date_max']}"
    )
    for col, n in report["missing_values"].items():
        if n:
            pct = 100 * n / len(df)
            logger.warning(f"QUALITÉ | {col} : {n} valeurs manquantes ({pct:.1f}%)")

    # Alerte si une ville n'a pas le même nombre de jours que les autres
    days_per_city = df.groupby("city")["forecast_date"].nunique()
    if days_per_city.nunique() > 1:
        logger.warning(
            f"QUALITÉ | Nombre de jours inégal entre villes "
            f"(min={days_per_city.min()}, max={days_per_city.max()})"
        )

    return report


# Orchestration

def run_silver(run_date: str | None = None) -> Path:
    run_date = run_date or date.today().isoformat()

    df = read_bronze_files(run_date)
    df = standardize(df)
    df = drop_duplicates(df)
    df = handle_inconsistencies(df)
    df = join_cities(df)
    quality_report(df)

    final_columns = [
        "city", "latitude", "longitude", "forecast_date",
        "temp_max", "temp_min", "precipitation_mm", "precipitation_prob",
        "wind_speed_max", "wind_gust_max", "weather_code", "extracted_at",
    ]
    df = df[[c for c in final_columns if c in df.columns]]
    df = df.sort_values(["city", "forecast_date"]).reset_index(drop=True)

    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    out_parquet = SILVER_DIR / f"weather_silver_{run_date}.parquet"
    out_csv = SILVER_DIR / f"weather_silver_{run_date}.csv"

    try:
        df.to_parquet(out_parquet, index=False)
        logger.info(f"Silver écrit : {out_parquet.name}")
    except Exception as e:
        logger.warning(f"Écriture parquet impossible ({e}), CSV uniquement")
        out_parquet = out_csv

    df.to_csv(out_csv, index=False)
    logger.info(f"Silver écrit : {out_csv.name} ({len(df)} lignes)")

    return out_parquet


if __name__ == "__main__":
    run_silver()

