-- Active: 1768245236744@@127.0.0.1@5432
-- Create Schemas for Medallion Architecture inside Postgres
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

----------------------------------------------------
-- SILVER LAYER: Cleaned & Standardized Weather Data
----------------------------------------------------
CREATE TABLE IF NOT EXISTS silver.weather (
    id SERIAL PRIMARY KEY,
    city_id INT NOT NULL,
    city_name VARCHAR(100) NOT NULL,
    country VARCHAR(10),
    latitude NUMERIC(8, 5),
    longitude NUMERIC(8, 5),
    temperature_celsius NUMERIC(5, 2),
    feels_like_celsius NUMERIC(5, 2),
    humidity INT,
    pressure_hpa INT,
    wind_speed_m_s NUMERIC(5, 2),
    weather_condition VARCHAR(100),
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT idx_city_timestamp UNIQUE (city_id, recorded_at)
);

----------------------------------------------------
-- GOLD LAYER: Aggregated Risk Scores & Analytics
----------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.daily_weather_summary (
    id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    avg_temp_celsius NUMERIC(5, 2),
    max_temp_celsius NUMERIC(5, 2),
    min_temp_celsius NUMERIC(5, 2),
    max_wind_speed NUMERIC(5, 2),
    avg_humidity NUMERIC(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT idx_city_date UNIQUE (city_name, date)
);

CREATE TABLE IF NOT EXISTS gold.weather_risk_scores (
    id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    risk_score NUMERIC(4, 2) NOT NULL, -- e.g. 0.00 to 10.00
    risk_level VARCHAR(20) NOT NULL,   -- 'LOW', 'MODERATE', 'HIGH', 'EXTREME'
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);