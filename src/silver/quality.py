import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

REQUIRED_COLUMNS = [
    "city_name", "latitude", "longitude", "date",
    "temp_max_celsius", "temp_min_celsius", "precipitation_mm",
    "precipitation_prob_pct", "wind_speed_max_kmh", "wind_gusts_max_kmh",
    "weather_code",
]

WMO_CODES = {
    0, 1, 2, 3, 45, 48, 51, 53, 55, 56, 57, 61, 63, 65, 66, 67,
    71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99,
}

NOT_NULL_COLUMNS = [
    "city_name", "date", "temp_max_celsius", "temp_min_celsius",
    "precipitation_mm", "wind_speed_max_kmh", "weather_code",
]


def _issue(check: str, count: int, detail: str) -> dict:
    return {"check": check, "issues": int(count), "detail": detail}