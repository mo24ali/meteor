import json

import pandas as pd

from src.silver.clean_weather import clean_bronze_snapshots, flatten_city_daily


def _result(city="Casablanca", lat=33.5992, lng=-7.62, n_days=7):
    return {
        "city": city,
        "latitude": lat,
        "longitude": lng,
        "ingested_at": "2026-09-15T12:00:00.000000",
        "raw_api_response": {
            "daily": {
                "time": [f"2026-09-{15 + i:02d}" for i in range(n_days)],
                "temperature_2m_max": [28.0 + i for i in range(n_days)],
                "temperature_2m_min": [20.0 + i for i in range(n_days)],
                "precipitation_sum": [0.0] * n_days,
                "precipitation_probability_max": [10] * n_days,
                "wind_speed_10m_max": [11.0] * n_days,
                "wind_gusts_10m_max": [31.0] * n_days,
                "weather_code": [0] * n_days,
            }
        },
    }


def _write_snapshot(tmp_path, run_id, results, day="2026-09-15"):
    day_dir = tmp_path / "bronze" / day
    day_dir.mkdir(parents=True, exist_ok=True)
    snapshot = {"run_id": run_id, "run_at": "2026-09-15T12:00:00", "results": results}
    path = day_dir / f"raw_weather_snapshot_{run_id}.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")
    return path


def test_flatten_city_daily_builds_one_row_per_day():
    df = flatten_city_daily(_result(n_days=7))
    assert df.shape == (7, 12)
    assert df["date"].nunique() == 7
    assert df["temp_max_celsius"].tolist() == [28.0, 29.0, 30.0, 31.0, 32.0, 33.0, 34.0]


def test_flatten_city_daily_includes_all_mapped_columns():
    df = flatten_city_daily(_result(n_days=7))
    for col in ["precipitation_mm", "precipitation_prob_pct", "wind_speed_max_kmh",
                 "wind_gusts_max_kmh", "weather_code"]:
        assert col in df.columns
    assert (df["wind_gusts_max_kmh"] == 31.0).all()


def test_flatten_city_daily_parses_dates():
    df = flatten_city_daily(_result(n_days=7))
    assert pd.api.types.is_datetime64_any_dtype(df["date"])


def test_clean_bronze_snapshots_empty_dir_returns_empty(tmp_path):
    df = clean_bronze_snapshots(str(tmp_path / "bronze"))
    assert df.empty