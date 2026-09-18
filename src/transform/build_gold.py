# feature engineering + risk_score 
from datetime import date
from pathlib import Path

import pandas as pd

from src.utils.config import GOLD_DIR, SILVER_DIR
from src.utils.logger import get_Logger

logger = get_Logger(__name__)

TEMP_COMFORT_MIN = 5.0
TEMP_COMFORT_MAX = 38.0
#précipitation
PRECIP_SATURATION_MM = 30.0   
WIND_SATURATION_KMH = 90.0 

QUALITY_CHECK_COLUMNS = ["temp_max", "precipitation_mm", "wind_gust_max", "weather_code"]

# Sévérité WMO (0=aucun risque, 4=risque maximal)
WMO_SEVERITY = {
    0: 0, 1: 0, 2: 0, 3: 0,                # ciel clair à couvert
    45: 2, 48: 2,                          # brouillard (visibilité réduite)
    51: 1, 53: 1, 55: 2,                   # bruine légère à dense
    56: 2, 57: 3,                          # bruine verglaçante
    61: 1, 63: 2, 65: 3,                   # pluie légère à forte
    66: 3, 67: 4,                          # pluie verglaçante
    71: 2, 73: 3, 75: 4, 77: 3,            # neige
    80: 2, 81: 3, 82: 4,                   # averses
    85: 3, 86: 4,                          # averses de neige
    95: 4, 96: 4, 99: 4,                   # orages
}
# Lecture Silver 

def read_silver(run_date: str | None = None) -> pd.DataFrame:
    run_date = run_date or date.today().isoformat()
    parquet_path = SILVER_DIR / f"weather_silver_{run_date}.parquet"
    csv_path = SILVER_DIR / f"weather_silver_{run_date}.csv"

    if parquet_path.exists():
        try:
            df = pd.read_parquet(parquet_path)
            logger.info(f"Silver lu depuis {parquet_path.name}")
            return df
        except Exception as e:
            logger.warning(f"Lecture parquet échouée ({e}), tentative CSV")

    if not csv_path.exists():
        raise FileNotFoundError(f"Aucun fichier Silver trouvé pour {run_date}")

    df = pd.read_csv(csv_path, parse_dates=["forecast_date", "extracted_at"])
    df["forecast_date"] = df["forecast_date"].dt.date
    logger.info(f"Silver lu depuis {csv_path.name}")
    return df


#  Catégories

def categorize_temperature(temp_max: float) -> str:
    if pd.isna(temp_max):
        return "Inconnu"
    if temp_max < 15:
        return "Froid"
    if temp_max < 30:
        return "Normal"
    if temp_max < 38:
        return "Chaud"
    return "Extrême"


def categorize_precipitation(mm: float) -> str:
    if pd.isna(mm):
        return "Inconnu"
    if mm == 0:
        return "Aucune"
    if mm < 5:
        return "Faible"
    if mm < 20:
        return "Modérée"
    return "Forte"


def categorize_wind(gust_kmh: float) -> str:
    if pd.isna(gust_kmh):
        return "Inconnu"
    if gust_kmh < 30:
        return "Calme"
    if gust_kmh < 50:
        return "Modéré"
    if gust_kmh < 70:
        return "Fort"
    return "Violent"

#  Risk Score

def compute_risk_score(row: pd.Series) -> float:

    # 1. Précipitations (35 pts)
    precip_mm = 0 if pd.isna(row["precipitation_mm"]) else row["precipitation_mm"]
    precip_prob = 0 if pd.isna(row["precipitation_prob"]) else row["precipitation_prob"]
    precip_score = (
        min(precip_mm, PRECIP_SATURATION_MM) / PRECIP_SATURATION_MM * 25
        + precip_prob / 100 * 10
    )

    # 2. Vent (30 pts) - basé sur les rafales
    gust = 0 if pd.isna(row["wind_gust_max"]) else row["wind_gust_max"]
    wind_score = min(gust, WIND_SATURATION_KMH) / WIND_SATURATION_KMH * 30

    # 3. Température extrême (15 pts)
    temp_max = row["temp_max"]
    if pd.isna(temp_max):
        temp_score = 0
    elif temp_max > TEMP_COMFORT_MAX:
        temp_score = min((temp_max - TEMP_COMFORT_MAX) * 1.5, 15)
    elif temp_max < TEMP_COMFORT_MIN:
        temp_score = min((TEMP_COMFORT_MIN - temp_max) * 1.5, 15)
    else:
        temp_score = 0

    # 4. Sévérité code météo WMO (20 pts)
    code = row["weather_code"]
    severity = WMO_SEVERITY.get(int(code), 2) if pd.notna(code) else 0
    code_score = severity * 5

    total = precip_score + wind_score + temp_score + code_score
    return round(min(total, 100), 1)

# flag 
def data_quality_flag(row: pd.Series) -> str:
   
    n_missing = sum(pd.isna(row[col]) for col in QUALITY_CHECK_COLUMNS)
    if n_missing == 0:
        return "Complet"
    if n_missing <= 2:
        return "Partiel"
    return "Manquant"

# risk level 

def risk_level(score: float) -> str:
    if score < 25:
        return "Faible"
    if score < 50:
        return "Modéré"
    if score < 75:
        return "Élevé"
    return "Critique"

# Orchestration 

def run_gold(run_date: str | None = None) -> Path:

    run_date = run_date or date.today().isoformat()
    df = read_silver(run_date)

    df["temp_category"] = df["temp_max"].apply(categorize_temperature)
    df["precipitation_category"] = df["precipitation_mm"].apply(categorize_precipitation)
    df["wind_category"] = df["wind_gust_max"].apply(categorize_wind)

    df["risk_score"] = df.apply(compute_risk_score, axis=1)
    df["risk_level"] = df["risk_score"].apply(risk_level)
    df["data_quality_flag"] = df.apply(data_quality_flag, axis=1)

    # Indicateurs temporels utiles pour le dashboard / les filtres
    df["forecast_date"] = pd.to_datetime(df["forecast_date"])
    df["day_of_week"] = df["forecast_date"].dt.day_name()
    # Ven/Sam 
    df["is_weekend"] = df["forecast_date"].dt.dayofweek.isin([4, 5])  
    df["days_ahead"] = (df["forecast_date"] - pd.Timestamp(run_date)).dt.days
    df["forecast_date"] = df["forecast_date"].dt.date

    n_high_risk = (df["risk_score"] >= 50).sum()
    top_city = df.groupby("city")["risk_score"].mean().idxmax()
    quality_counts = df["data_quality_flag"].value_counts().to_dict()
    logger.info(
        f"GOLD | {len(df)} lignes | risk_score moyen={df['risk_score'].mean():.1f} | "
        f"{n_high_risk} lignes à risque Élevé/Critique | ville la + à risque en moyenne : {top_city}"
    )
    logger.info(f"GOLD | qualité des données : {quality_counts}")
    n_unreliable = quality_counts.get("Manquant", 0)
    if n_unreliable:
        logger.warning(
            f"GOLD | {n_unreliable} lignes avec données insuffisantes "
            f"(flag 'Manquant') -> risk_score peu fiable pour ces lignes"
        )

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = GOLD_DIR / f"weather_gold_{run_date}.csv"
    out_parquet = GOLD_DIR / f"weather_gold_{run_date}.parquet"

    df.to_csv(out_csv, index=False)
    try:
        df.to_parquet(out_parquet, index=False)
        logger.info(f"Gold écrit : {out_parquet.name}")
        return out_parquet
    except Exception:
        logger.info(f"Gold écrit : {out_csv.name} (parquet indisponible)")
        return out_csv


if __name__ == "__main__":
    run_gold()



