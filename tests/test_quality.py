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


def test_run_quality_checks_detects_nulls_and_dupes():
    df = _good_df()
    df.loc[0, "temp_max_celsius"] = None
    df = pd.concat([df, df.iloc[:1]], ignore_index=True)

    report = run_quality_checks(df)
    checks = report["check"].tolist()
    assert "no_null" in checks
    assert "city_date_unique" in checks


def test_run_quality_checks_detects_inverted_minmax_and_invalid_code():
    df = _good_df()
    df.loc[0, ["temp_min_celsius", "temp_max_celsius"]] = [30.0, 20.0]
    df.loc[1, "weather_code"] = 999

    report = run_quality_checks(df)
    checks = report.set_index("check")["issues"].to_dict()
    assert checks["temp_min_le_max"] == 1
    assert checks["wmo_code_valid"] == 1