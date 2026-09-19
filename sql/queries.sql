-- ============================================================
-- Meteor — Étape 4 : Analyse SQL (gold.daily_weather_summary)
-- 5 requêtes métier
-- ============================================================

-- Q1. Quelles villes auront les températures les plus élevées ?
-- Top 10 des villes par température maximale sur la période.
SELECT
    city_name,
    date,
    temp_max_celsius,
    temp_category
FROM gold.daily_weather_summary
ORDER BY temp_max_celsius DESC
LIMIT 10;

-- Q2. Quelles villes auront les plus fortes précipitations ?
-- Top 10 des villes par cumul de précipitations sur la période.
SELECT
    city_name,
    SUM(precipitation_mm) AS total_precip_mm,
    MAX(precipitation_mm)  AS max_daily_precip_mm
FROM gold.daily_weather_summary
GROUP BY city_name
ORDER BY total_precip_mm DESC
LIMIT 10;

-- Q3. Quelles villes présentent le risque moyen le plus élevé ?
SELECT
    city_name,
    ROUND(AVG(risk_score), 2) AS avg_risk_score,
    COUNT(*) AS days
FROM gold.daily_weather_summary
GROUP BY city_name
ORDER BY avg_risk_score DESC
LIMIT 10;

-- Q4. Quelles périodes présentent le risque maximal ?
-- Journées à risque élevé/extrême, classées par risque décroissant.
SELECT
    date,
    COUNT(*) FILTER (WHERE risk_level IN ('HIGH', 'EXTREME')) AS risky_cities,
    ROUND(AVG(risk_score), 2) AS avg_risk_score,
    MAX(risk_score) AS max_risk_score
FROM gold.daily_weather_summary
GROUP BY date
ORDER BY risky_cities DESC, avg_risk_score DESC;

-- Q5. Pour chaque ville, quelle période présente le plus grand risque ?
-- Fonction de fenêtrage : date du risque maximum par ville.
WITH ranked AS (
    SELECT
        city_name,
        date,
        risk_score,
        ROW_NUMBER() OVER (PARTITION BY city_name ORDER BY risk_score DESC, date) AS rn
    FROM gold.daily_weather_summary
)
SELECT
    city_name,
    date   AS worst_date,
    risk_score
FROM ranked
WHERE rn = 1
ORDER BY risk_score DESC
LIMIT 10;