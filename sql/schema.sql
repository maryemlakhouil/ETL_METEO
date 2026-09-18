-- la table villes 

CREATE TABLE IF NOT EXISTS villes (
    city_id  SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL UNIQUE,
    latitude  DOUBLE PRECISION NOT NULL,
    longitude  DOUBLE PRECISION NOT NULL
);

-- la table privisions 

CREATE TABLE IF NOT EXISTS previsions_meteo (
    prevision_id  SERIAL PRIMARY KEY,
    city_id        INTEGER NOT NULL REFERENCES villes(city_id) ON DELETE CASCADE,
    forecast_date  DATE NOT NULL,
    temp_max       NUMERIC(5,2),
    temp_min       NUMERIC(5,2),
    precipitation_mm  NUMERIC(6,2),
    precipitation_prob NUMERIC(5,2),
    wind_speed_max    NUMERIC(5,2),
    wind_gust_max    NUMERIC(5,2),
    weather_code    INTEGER,
    temp_category    VARCHAR(20),
    precipitation_category  VARCHAR(20),
    wind_category         VARCHAR(20),
    risk_score      NUMERIC(5,2) NOT NULL,
    risk_level     VARCHAR(20) NOT NULL,
    data_quality_flag  VARCHAR(20) NOT NULL,
    extracted_at    TIMESTAMP,
    loaded_at    TIMESTAMP NOT NULL DEFAULT now(),

    CONSTRAINT uq_city_forecast_date UNIQUE (city_id, forecast_date)
);

-- bonus historique 

CREATE TABLE IF NOT EXISTS previsions_historique (
    historique_id  SERIAL PRIMARY KEY,
    city_id     INTEGER NOT NULL REFERENCES villes(city_id) ON DELETE CASCADE,
    forecast_date DATE NOT NULL,
    temp_max   NUMERIC(5,2),
    temp_min   NUMERIC(5,2),
    precipitation_mm  NUMERIC(6,2),
    precipitation_prob  NUMERIC(5,2),
    wind_speed_max   NUMERIC(5,2),
    wind_gust_max    NUMERIC(5,2),
    weather_code    INTEGER,
    risk_score   NUMERIC(5,2),
    risk_level   VARCHAR(20),
    data_quality_flag  VARCHAR(20),
    extracted_at  TIMESTAMP,
    recorded_at TIMESTAMP NOT NULL DEFAULT now()
);

-- index 

CREATE INDEX IF NOT EXISTS idx_previsions_forecast_date ON previsions_meteo (forecast_date);
CREATE INDEX IF NOT EXISTS idx_previsions_risk_score    ON previsions_meteo (risk_score);
CREATE INDEX IF NOT EXISTS idx_previsions_city          ON previsions_meteo (city_id);
CREATE INDEX IF NOT EXISTS idx_historique_city_date   ON previsions_historique (city_id, forecast_date);
