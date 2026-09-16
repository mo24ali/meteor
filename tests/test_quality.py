import pandas as pd

from src.silver.quality import log_quality_report, run_quality_checks


def _good_df():
    return pd.DataFrame(
        {
            "city_name": ["Casablanca", "Rabat"],
            "latitude": [33.5992, 34.0209],
            "longitude": [-7.62, -6.8416],
            "date": pd.to_datetime(["2026-09-15", "2026-09-15"]),
            "temp_max_celsius": [28.7, 26.0],
            "temp_min_celsius": [21.7, 18.0],
            "precipitation_mm": [0.0, 5.0],
            "precipitation_prob_pct": [10, 40],
            "wind_speed_max_kmh": [11.0, 20.0],
            "wind_gusts_max_kmh": [31.0, 40.0],
            "weather_code": [0, 61],
        }
    )


def test_run_quality_checks_clean_data_has_no_issues():
    report = run_quality_checks(_good_df())
    assert report.empty