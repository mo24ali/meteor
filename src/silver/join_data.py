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


def load_city_metadata(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    missing = [col for col in CITY_META_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Cities file is missing required columns: {missing}")

    return (
        df[CITY_META_COLUMNS]
        .dropna(subset=["city"])
        .drop_duplicates(subset=["city"], keep="first")
        .reset_index(drop=True)
    )


def enrich_weather_with_cities(
    weather_csv: str,
    cities_csv: str,
    output_csv: str,
) -> pd.DataFrame:
    weather = pd.read_csv(weather_csv)
    weather["date"] = pd.to_datetime(weather["date"])

    cities = load_city_metadata(cities_csv)
    merged = weather.merge(cities, left_on="city_name", right_on="city", how="left")

    unmatched = merged.loc[merged["country"].isna(), "city_name"].drop_duplicates().tolist()
    if unmatched:
        logger.warning(
            "No city metadata found for %d city(ies): %s",
            len(unmatched),
            ", ".join(unmatched),
        )

    merged = merged.drop(columns=["city"]).reindex(columns=SILVER_ORDER)

    out_path = Path(output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(out_path, index=False)

    logger.info(
        "Enriched silver weather: %d rows (%.0f%%) with matched city metadata -> %s",
        len(merged),
        100 * (1 - merged["country"].isna().mean()),
        out_path,
    )
    return merged


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Silver layer: join cleaned weather with city metadata."
    )
    parser.add_argument(
        "--weather-csv", default="data/silver/weather.csv", help="Cleaned weather CSV"
    )
    parser.add_argument(
        "--cities-csv", default="data/raw_cities/cities.csv", help="Cities metadata CSV"
    )
    parser.add_argument(
        "--output-csv", default="data/silver/weather_enriched.csv", help="Enriched output CSV"
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    enrich_weather_with_cities(
        weather_csv=args.weather_csv,
        cities_csv=args.cities_csv,
        output_csv=args.output_csv,
    )