from datetime import date, timedelta

import pandas as pd

RISK_LEVELS = ["Faible", "Modéré", "Élevé", "Critique"]
RISKY_LEVELS = ["Élevé", "Critique"]
PERIOD_PRESETS = {
    "Toutes les dates disponibles": None,
    "Aujourd'hui": 0,
    "3 prochains jours": 3,
    "7 prochains jours": 7,
}
RISK_COLORS = {
    "Faible": "#16a34a",    
    "Modéré": "#ca8a04",    
    "Élevé": "#ea580c",     
    "Critique": "#dc2626", 
}


def compute_period_range(preset: str, today: date, min_date: date, max_date: date) -> tuple:
   
    n_days = PERIOD_PRESETS.get(preset)
    if n_days is None:
        return (min_date, max_date)

    start = max(today, min_date)
    end = min(today + timedelta(days=max(n_days - 1, 0)), max_date)

    if start > end:
        return (min_date, max_date)
    return (start, end)


def apply_filters(df: pd.DataFrame, cities: list, date_range: tuple, risk_levels: list) -> pd.DataFrame:
    filtered = df.copy()
    if cities:
        filtered = filtered[filtered["city_name"].isin(cities)]
    if date_range and len(date_range) == 2:
        start, end = date_range
        filtered = filtered[(filtered["forecast_date"] >= start) & (filtered["forecast_date"] <= end)]
    if risk_levels:
        filtered = filtered[filtered["risk_level"].isin(risk_levels)]
    return filtered


def compute_kpis(df: pd.DataFrame) -> dict:
    if df.empty:
        return dict(n_cities=0, temp_max=None, precip_max=None, n_risky=0, top_city=None)
    return dict(
        n_cities=df["city_name"].nunique(),
        temp_max=df["temp_max"].max(),
        precip_max=df["precipitation_mm"].max(),
        n_risky=int(df["risk_level"].isin(RISKY_LEVELS).sum()),
        top_city=df.groupby("city_name")["risk_score"].mean().idxmax(),
    )
