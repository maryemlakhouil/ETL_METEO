-- les 5 quieries de brief jours
-- Q1 : Quelles villes auront les températures les plus élevées  dans les prochains  ?
-- temperature maximale moyenne pour chaque ville 
    SELECT v.city_name,ROUND(AVG(p.temp_max),2) AS temp_max_moyenne,MAX(p.temp_max) AS temp_max_pic
    FROM previsions_meteo p
    JOIN villes v ON v.city_id = p.city_id
    GROUP BY v.city_name
    ORDER BY temp_max_moyenne DESC
    LIMIT 10;

-- Quelles villes auront les plus fortes précipitations ?

SELECT v.city_name,
    SUM(p.precipitation_mm) AS precipitation_cumulee_mm,
    AVG(p.precipitation_prob) AS probabilite_moyenne_pct
FROM previsions_meteo p
JOIN villes v ON v.city_id = p.city_id
GROUP BY v.city_name
HAVING SUM(p.precipitation_mm) > 0
ORDER BY precipitation_cumulee_mm DESC
LIMIT 10;

-- 3 - Trouver les villes qui ont le risque moyen le plus élevé.

SELECT v.city_name, AVG(p.risk_score) AS risk_score_moyen,
    COUNT(*) FILTER (WHERE p.risk_level IN ('Élevé', 'Critique')) AS jours_a_risque
FROM previsions_meteo p
JOIN villes v ON v.city_id = p.city_id
GROUP BY v.city_name
ORDER BY risk_score_moyen DESC
LIMIT 10;

-- Q4 : Quelles périodes (dates) présentent le risque MAXIMAL,

SELECT
    p.forecast_date,AVG(p.risk_score) AS risk_score_moyen,
    COUNT(*) FILTER (WHERE p.risk_level IN ('Élevé', 'Critique')) AS villes_a_risque
FROM previsions_meteo p
GROUP BY p.forecast_date
ORDER BY risk_score_moyen DESC;


-- Q5 : Pour CHAQUE ville, quelle est la période présentant le plus
--      grand risque ? (BONUS : window function RANK())
--
-- On ne peut pas faire ça avec un simple GROUP BY (on perdrait la
-- date associée au max). RANK() OVER (PARTITION BY ville) permet de
-- classer les jours de chaque ville par risque décroissant, puis on
-- ne garde que le rang 1 de chaque ville.
-- ------------------------------------------------------------------
SELECT city_name, forecast_date, risk_score, risk_level
FROM (
    SELECT v.city_name, p.forecast_date, p.risk_score, p.risk_level,
        RANK() OVER (
            PARTITION BY v.city_name
            ORDER BY p.risk_score DESC
        ) AS rang_risque
    FROM previsions_meteo p
    JOIN villes v ON v.city_id = p.city_id
) classement
WHERE rang_risque = 1
ORDER BY risk_score DESC;

