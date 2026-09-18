import sys
from datetime import date as date_cls
from pathlib import Path
# directement depuis dashboard/ (son propre dossier, pas la racine).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

from dashboard.logic import (PERIOD_PRESETS,RISK_COLORS,RISK_LEVELS,apply_filters,build_map_data,compute_kpis,compute_period_range,)
from src.utils.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

st.set_page_config(page_title="Météo Livraison - Maroc", layout="wide")

# Couleurs des cartes KPI 
KPI_COLOR_INFO = "#2563eb"     
KPI_COLOR_WARNING = "#ea580c"  
KPI_COLOR_DANGER = "#dc2626"  


def kpi_card(label: str, value: str, color: str) -> None:
    
    st.markdown(
        f"""
        <div style="
            background-color: {color}18;
            border-left: 5px solid {color};
            border-radius: 8px;
            padding: 12px 16px;
            height: 90px;
        ">
            <div style="font-size: 13px; color: #555; margin-bottom: 4px;">{label}</div>
            <div style="font-size: 26px; font-weight: 700; color: {color};">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def style_risk_level(val: str) -> str:
    color = RISK_COLORS.get(val)
    if not color:
        return ""
    return f"background-color: {color}22; color: {color}; font-weight: 600;"

@st.cache_resource
def get_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    query = """
        SELECT
            v.city_name, v.latitude, v.longitude,
            p.forecast_date, p.temp_max, p.temp_min,
            p.precipitation_mm, p.precipitation_prob, p.wind_speed_max,
            p.wind_gust_max, p.weather_code, p.temp_category,
            p.precipitation_category, p.wind_category,
            p.risk_score, p.risk_level, p.data_quality_flag
        FROM previsions_meteo p
        JOIN villes v ON v.city_id = p.city_id
        ORDER BY v.city_name, p.forecast_date
    """
    df = pd.read_sql(query, get_engine())
    df["forecast_date"] = pd.to_datetime(df["forecast_date"]).dt.date
    return df


def main():
    st.title("Suivi météo & risques livraison — Maroc")
    st.caption("Où et quand faut-il être particulièrement vigilant dans les prochains jours ?")

    try:
        df = load_data()
    except Exception as e:
        st.error(f"Impossible de se connecter à PostgreSQL : {e}")
        st.info("Vérifie que le pipeline a bien été lancé (extract → silver → gold → load) "
                "et que les variables d'environnement POSTGRES_* sont correctes.")
        st.stop()

    if df.empty:
        st.warning("Aucune donnée en base. Lance le pipeline avant d'ouvrir ce dashboard.")
        st.stop()

    # --- Filtres ---
    st.sidebar.header("Filtres")
    all_cities = sorted(df["city_name"].unique())
    selected_cities = st.sidebar.multiselect("Ville", all_cities, default=[])

    min_date, max_date = df["forecast_date"].min(), df["forecast_date"].max()

    period_choice = st.sidebar.selectbox("Période", list(PERIOD_PRESETS.keys()))
    default_range = compute_period_range(period_choice, date_cls.today(), min_date, max_date)

    date_range = st.sidebar.date_input(
        "Dates (ajustable)", value=default_range, min_value=min_date, max_value=max_date,
        help="Pré-rempli selon la 'Période' choisie ci-dessus, modifiable manuellement.",
    )
    if not (isinstance(date_range, tuple) and len(date_range) == 2):
        date_range = default_range

    selected_levels = st.sidebar.multiselect("Niveau de risque", RISK_LEVELS, default=[])

    filtered = apply_filters(df, selected_cities, date_range, selected_levels)

    # --- (cartes colorées) ---

    kpis = compute_kpis(filtered)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("Villes couvertes", str(kpis["n_cities"]), KPI_COLOR_INFO)
    with c2:
        val = f"{kpis['temp_max']:.1f} °C" if kpis["temp_max"] is not None else "N/A"
        kpi_card("Température max", val, KPI_COLOR_WARNING)
    with c3:
        val = f"{kpis['precip_max']:.1f} mm" if kpis["precip_max"] is not None else "N/A"
        kpi_card("Précipitations max", val, KPI_COLOR_INFO)
    with c4:
        kpi_card("Périodes à risque", str(kpis["n_risky"]), KPI_COLOR_DANGER)
    with c5:
        kpi_card("Ville la + à risque", kpis["top_city"] or "N/A", KPI_COLOR_DANGER)

    st.divider()

    # --- Carte (vue d'ensemble géographique en premier) ---
    st.subheader("Carte des risques")
    map_df = build_map_data(filtered)
    if map_df.empty:
        st.info("Aucune donnée géolocalisée pour ces filtres.")
    else:
        fig = px.scatter_map(
            map_df,
            lat="latitude",
            lon="longitude",
            color="risk_level",
            size="risk_score",
            size_max=28,
            hover_name="city_name",
            hover_data={
                "latitude": False,
                "longitude": False,
                "risk_score": True,
                "temp_max": True,
                "precipitation_mm": True,
                "n_previsions": True,
            },
            color_discrete_map=RISK_COLORS,
            category_orders={"risk_level": RISK_LEVELS},
            zoom=4.4,
            center={"lat": 31.5, "lon": -6.5},  
            map_style="open-street-map",
            height=480,
        )
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Chaque point = risque moyen d'une ville sur la période filtrée. "
            "Taille et couleur augmentent avec le niveau de risque."
        )

    st.divider()

    # --- Risque par ville 
    col_bar, col_line = st.columns(2)

    with col_bar:
        st.subheader("Risque moyen par ville")
        by_city = filtered.groupby("city_name")["risk_score"].mean().sort_values(ascending=False).head(15)
        st.bar_chart(by_city)

    with col_line:
        st.subheader("Évolution du risque")
        if selected_cities:
            pivot = filtered.pivot_table(index="forecast_date", columns="city_name", values="risk_score")
            st.line_chart(pivot)
        else:
            st.info("Sélectionne une ou plusieurs villes dans le filtre pour voir l'évolution du risque.")

    st.divider()

    # --- Détail (tableau complet, en bas) ---
    st.subheader(" Détail des prévisions")
    detail_cols = [
        "city_name", "forecast_date", "temp_max", "precipitation_mm",
        "wind_gust_max", "risk_score", "risk_level", "data_quality_flag",
    ]
    detail_df = filtered.sort_values("risk_score", ascending=False)[detail_cols]
    st.dataframe(
        detail_df.style.map(style_risk_level, subset=["risk_level"]),
        use_container_width=True,
        hide_index=True,
    )


if __name__ == "__main__":
    main()
