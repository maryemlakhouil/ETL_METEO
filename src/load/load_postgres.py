from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extras as pg_extras
from psycopg2.extensions import register_adapter, AsIs


register_adapter(np.int64, lambda val: AsIs(int(val)))
register_adapter(np.float64, lambda val: AsIs(float(val)))

from src.utils.config import (
    DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER,
    GOLD_DIR, SCHEMA_SQL_PATH,
)
from src.utils.logger import get_Logger

logger = get_Logger(__name__)

FORECAST_COLUMNS = [
    "temp_max", "temp_min", "precipitation_mm", "precipitation_prob",
    "wind_speed_max", "wind_gust_max", "weather_code",
    "temp_category", "precipitation_category", "wind_category",
    "risk_score", "risk_level", "data_quality_flag", "extracted_at",
]

#  Connexion

def get_connection():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
    )


def ensure_schema(conn) -> None:
    with open(SCHEMA_SQL_PATH, encoding="utf-8") as f:
        schema_sql = f.read()
    with conn.cursor() as cur:
        cur.execute(schema_sql)
    conn.commit()
    logger.info("Schéma vérifié/créé")


#  Lecture Gold
def read_gold(run_date: str | None = None) -> pd.DataFrame:
    run_date = run_date or date.today().isoformat()
    parquet_path = GOLD_DIR / f"weather_gold_{run_date}.parquet"
    csv_path = GOLD_DIR / f"weather_gold_{run_date}.csv"

    if parquet_path.exists():
        try:
            return pd.read_parquet(parquet_path)
        except Exception:
            pass

    if not csv_path.exists():
        raise FileNotFoundError(f"Aucun fichier Gold trouvé pour {run_date}")
    df = pd.read_csv(csv_path)
    df["forecast_date"] = pd.to_datetime(df["forecast_date"]).dt.date
    df["extracted_at"] = pd.to_datetime(df["extracted_at"], errors="coerce")
    return df

#   retourne {city_name: city_id}
def upsert_cities(conn, df: pd.DataFrame) -> dict[str, int]:
   
    cities = (
        df[["city", "latitude", "longitude"]]
        .drop_duplicates(subset=["city"])
        .dropna(subset=["city"])
    )
    rows = list(cities.itertuples(index=False, name=None))

    query = """
        INSERT INTO villes (city_name, latitude, longitude)
        VALUES %s
        ON CONFLICT (city_name) DO UPDATE
            SET latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude
        RETURNING city_id, city_name
    """
    with conn.cursor() as cur:
        results = pg_extras.execute_values(cur, query, rows, fetch=True)
    conn.commit()

    city_map = {name: city_id for city_id, name in results}
    logger.info(f"{len(city_map)} villes upsertées")
    return city_map


#  Prévisions

def upsert_forecasts(conn, df: pd.DataFrame, city_map: dict[str, int]) -> int:

    df = df.copy()
    df["city_id"] = df["city"].map(city_map)

    missing = df["city_id"].isna().sum()
    if missing:
        logger.warning(f"{missing} lignes ignorées : ville non trouvée dans city_map")
        df = df.dropna(subset=["city_id"])

    columns = ["city_id", "forecast_date"] + FORECAST_COLUMNS

    rows = [
        #Pandas NaN -> PostgreSQL NULL
        tuple(None if pd.isna(v) else v for v in row)
        for row in df[columns].itertuples(index=False, name=None)
    ]

    set_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in FORECAST_COLUMNS)
    query = f"""
        INSERT INTO previsions_meteo ({", ".join(columns)})
        VALUES %s
        ON CONFLICT (city_id, forecast_date) DO UPDATE
            SET {set_clause}, loaded_at = now()
    """
    with conn.cursor() as cur:
        pg_extras.execute_values(cur, query, rows)
    conn.commit()

    logger.info(f"{len(rows)} prévisions upsertées dans previsions_meteo")
    return len(rows)


#  Orchestration
def run_load(run_date: str | None = None) -> None:
    run_date = run_date or date.today().isoformat()
    df = read_gold(run_date)

    conn = get_connection()
    try:
        ensure_schema(conn)
        city_map = upsert_cities(conn, df)
        n_forecasts = upsert_forecasts(conn, df, city_map)
        logger.info(f"Chargement terminé : {n_forecasts} prévisions ")
    finally:
        conn.close()


if __name__ == "__main__":
    run_load()
