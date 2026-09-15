import argparse
import json
import os
import time
from datetime import datetime
from typing import List, Optional, Set

import requests

from src.bronze.fetch_cities import load_moroccan_cities
from src.utils.logger import get_logger

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = 10
RATE_LIMIT_DELAY = 1.2

DAILY_FIELDS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "precipitation_probability_max",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "weather_code",
]

logger = get_logger(__name__)


def validate_payload(payload: dict) -> None:
    daily = payload.get("daily")
    if not isinstance(daily, dict) or "time" not in daily:
        raise ValueError(f"Unexpected response shape; missing 'daily.time': {sorted(payload)}")
    if "time" not in daily or not isinstance(daily["time"], list):
        raise ValueError(f"Unexpected response shape; 'daily.time' must be a list")


def fetch_weather_for_city(
    lat: float,
    lng: float,
    timeout: int = REQUEST_TIMEOUT,
    retries: int = 3,
    backoff_factor: float = 2.0,
) -> dict:
    params = {
        "latitude": lat,
        "longitude": lng,
        "daily": DAILY_FIELDS,
        "timezone": "auto",
    }

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(OPEN_METEO_URL, params=params, timeout=timeout)
            response.raise_for_status()
            payload = response.json()
            validate_payload(payload)
            return payload
        except requests.exceptions.RequestException as exc:
            logger.warning("Attempt %d failed for lat=%s lng=%s: %s", attempt, lat, lng, exc)
            if attempt == retries:
                raise
            time.sleep(backoff_factor**attempt)


def snapshot_path(output_dir: str, date_str: str, run_ts: datetime) -> str:
    day_dir = os.path.join(output_dir, date_str)
    os.makedirs(day_dir, exist_ok=True)
    run_id = run_ts.strftime("%Y%m%d_%H%M%S")
    return os.path.join(day_dir, f"raw_weather_snapshot_{run_id}.json")


def already_ingested_cities(day_dir: str) -> Set[str]:
    seen: Set[str] = set()
    if not os.path.isdir(day_dir):
        return seen
    for filename in os.listdir(day_dir):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(day_dir, filename)
        try:
            with open(filepath, encoding="utf-8") as f:
                snapshot = json.load(f)
        except (json.JSONDecodeError, OSError):
            logger.warning("Skipping unreadable snapshot %s", filepath)
            continue
        for entry in snapshot.get("results", []):
            city = entry.get("city")
            if city:
                seen.add(city)
    return seen


def run_bronze_ingestion(
    cities_csv: str = "data/raw_cities/cities.csv",
    output_dir: str = "data/bronze",
    resume: bool = False,
) -> int:
    cities_df = load_moroccan_cities(cities_csv)
    logger.info("Loaded %d cities for weather ingestion", len(cities_df))

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    day_dir = os.path.join(output_dir, date_str)

    already_done: Set[str] = already_ingested_cities(day_dir) if resume else set()
    if already_done:
        logger.info("Resume mode: %d cities already ingested, skipping them", len(already_done))

    results: List[dict] = []
    failed: List[str] = []
    skipped = 0

    for _, row in cities_df.iterrows():
        city_name = str(row["city"])
        lat, lng = float(row["lat"]), float(row["lng"])

        if city_name in already_done:
            skipped += 1
            continue

        logger.info("Ingesting weather data for %s (%.4f, %.4f)...", city_name, lat, lng)
        try:
            raw_data = fetch_weather_for_city(lat, lng)
            results.append(
                {
                    "city": city_name,
                    "latitude": lat,
                    "longitude": lng,
                    "ingested_at": datetime.now().isoformat(),
                    "raw_api_response": raw_data,
                }
            )
            time.sleep(RATE_LIMIT_DELAY)
        except Exception as err:
            logger.error("Skipped %s due to persistent error: %s", city_name, err)
            failed.append(city_name)

    file_path = snapshot_path(output_dir, date_str, now)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "run_id": now.strftime("%Y%m%d_%H%M%S"),
                "run_at": now.isoformat(),
                "total_cities": len(cities_df),
                "ingested": len(results),
                "skipped": skipped,
                "failed": failed,
                "results": results,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    logger.info(
        "Bronze ingestion complete: %d ingested, %d skipped, %d failed -> %s",
        len(results),
        skipped,
        len(failed),
        file_path,
    )
    return len(failed)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bronze layer: ingest raw weather data for Moroccan cities.")
    parser.add_argument("--cities", default="data/raw_cities/cities.csv", help="Path to cities CSV file")
    parser.add_argument("--output-dir", default="data/bronze", help="Root output directory for raw snapshots")
    parser.add_argument("--resume", action="store_true", help="Skip cities already present in today's snapshots")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    run_bronze_ingestion(
        cities_csv=args.cities,
        output_dir=args.output_dir,
        resume=args.resume,
    )