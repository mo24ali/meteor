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

def clean_bronze_snapshots(bronze_dir: str) -> pd.DataFrame:
    files = sorted(Path(bronze_dir).rglob("raw_weather_snapshot_*.json"))
    all_rows = []

    for f in files:
        with open(f, encoding="utf-8") as fh:
            snapshot = json.load(fh)
        for result in snapshot.get("results", []):
            df = flatten_city_daily(result)
            df["snapshot_run_id"] = snapshot["run_id"]
            all_rows.append(df)

    combined = pd.concat(all_rows, ignore_index=True)

    combined = (
        combined
        .sort_values(["date", "ingested_at"])
        .drop_duplicates(subset=["city_name", "date"], keep="last")
        .sort_values(["date", "city_name"])
        .reset_index(drop=True)
    )

    logger.info("Silver weather rows after cleaning: %d", len(combined))

    return combined