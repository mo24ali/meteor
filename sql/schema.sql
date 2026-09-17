-- Active: 1768245236744@@127.0.0.1@5432
-- Create Schemas for Medallion Architecture inside Postgres
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

----------------------------------------------------
-- SILVER LAYER: Cleaned & Standardized Weather Data
-- (daily forecast, one row per city per day)
----------------------------------------------------
CREATE TABLE IF NOT EXISTS silver.weather (
    city_name VARCHAR(100) NOT NULL,
    latitude NUMERIC(8, 5),
    longitude NUMERIC(8, 5),
    country VARCHAR(20),
    admin_name VARCHAR(100),
    date DATE NOT NULL,
    temp_max_celsius NUMERIC(5, 2),
    temp_min_celsius NUMERIC(5, 2),
    precipitation_mm NUMERIC(6, 2),
    precipitation_prob_pct INT,
    wind_speed_max_kmh NUMERIC(6, 2),
    wind_gusts_max_kmh NUMERIC(6, 2),
    weather_code INT,
    ingested_at TIMESTAMP WITH TIME ZONE,
    snapshot_run_id VARCHAR(20),
    CONSTRAINT idx_silver_city_date UNIQUE (city_name, date)
);

----------------------------------------------------
-- GOLD LAYER: Aggregated Risk Scores & Analytics
----------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.daily_weather_summary (
    city_name VARCHAR(100) NOT NULL,
    latitude NUMERIC(8, 5),
    longitude NUMERIC(8, 5),
    country VARCHAR(20),
    admin_name VARCHAR(100),
    date DATE NOT NULL,
    temp_max_celsius NUMERIC(5, 2),
    temp_min_celsius NUMERIC(5, 2),
    precipitation_mm NUMERIC(6, 2),
    temp_category VARCHAR(20),
    precip_category VARCHAR(20),
    wind_category VARCHAR(20),
    season VARCHAR(20),
    is_weekend BOOLEAN,
    risk_score NUMERIC(5, 2) NOT NULL,
    risk_level VARCHAR(10) NOT NULL,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT idx_gold_city_date UNIQUE (city_name, date)
);