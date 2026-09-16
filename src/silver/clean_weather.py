import json
import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger
logger = get_logger(__name__)

SILVER_COLUMNS = [
    "city_name", "latitude", "longitude", "date",
    "temp_max_celsius", "temp_min_celsius",
    "precipitation_mm", "precipitation_prob_pct",
    "wind_speed_max_kmh", "wind_gusts_max_kmh",
    "weather_code", "ingested_at", "snapshot_run_id"
]


COLUMN_MAP = {
    "temperature_2m_max": "temp_max_celsius",
    "temperature_2m_min": "temp_min_celsius",
    "precipitation_sum": "precipitation_mm",
    "precipitation_probability_max": "precipitation_prob_pct",
    "wind_speed_10m_max": "wind_speed_max_kmh",
    "wind_gusts_10m_max": "wind_gusts_max_kmh",
}


def flatten_city_daily(result: dict) -> pd.DataFrame:
    raw = result["raw_api_response"]["daily"]

    rows = []
    for i, day in enumerate(raw["time"]):
        row = {
            "city_name": result["city"],
            "latitude": result["latitude"],
            "longitude": result["longitude"],
            "date": pd.to_datetime(day),
            "weather_code": raw["weather_code"][i],
            "ingested_at": result["ingested_at"],
        }
        for raw_col, silver_col in COLUMN_MAP.items():
            row[silver_col] = raw[raw_col][i]
        rows.append(row)

    return pd.DataFrame(rows)