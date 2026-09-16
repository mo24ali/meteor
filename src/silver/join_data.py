import argparse
from pathlib import Path

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

CITY_META_COLUMNS = ["city", "country", "admin_name"]

SILVER_ORDER = [
    "city_name", "latitude", "longitude", "country", "admin_name", "date",
    "temp_max_celsius", "temp_min_celsius", "precipitation_mm",
    "precipitation_prob_pct", "wind_speed_max_kmh", "wind_gusts_max_kmh",
    "weather_code", "ingested_at", "snapshot_run_id",
]