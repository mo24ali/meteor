import pandas as pd

from src.gold.risk_score import (
    add_categories,
    build_gold_dataset,
    compute_risk_score,
    precip_score,
    risk_level,
    temp_score,
    wind_score,
    wmo_severity,
)


def test_temp_score_thresholds():
    assert temp_score(30) == 0.0
    assert temp_score(35) == 50.0
    assert temp_score(40) == 100.0
    assert temp_score(42) == 100.0


def test_precip_score_thresholds():
    assert precip_score(0) == 0.0
    assert precip_score(0.5) == 0.0
    assert precip_score(25) == 50.0
    assert precip_score(50) == 100.0
    assert precip_score(80) == 100.0


def test_wind_score_thresholds():
    assert wind_score(10) == 0.0
    assert wind_score(20) == 0.0
    assert wind_score(60) == 50.0
    assert wind_score(100) == 100.0
    assert wind_score(120) == 100.0


def test_wmo_severity_mapping():
    assert wmo_severity(0) == 0.0
    assert wmo_severity(95) == 90.0
    assert wmo_severity(99) == 100.0
    assert wmo_severity(48) == 30.0


def test_risk_level_boundaries():
    assert risk_level(34.99) == "LOW"
    assert risk_level(35.0) == "MODERATE"
    assert risk_level(55.0) == "HIGH"
    assert risk_level(75.0) == "EXTREME"
    assert risk_level(100.0) == "EXTREME"


def test_compute_risk_score_formula():
    row = {
        "temp_max_celsius": 35.0,
        "precipitation_mm": 0.0,
        "wind_speed_max_kmh": 20.0,
        "weather_code": 0,
    }
    score, level = compute_risk_score(row)
    assert score == 15.0
    assert level == "LOW"


def _clim_row(date="2026-09-19"):
    return {
        "city_name": ["Casablanca"],
        "latitude": [33.5992],
        "longitude": [-7.62],
        "country": ["Morocco"],
        "admin_name": ["Casablanca-Settat"],
        "date": [date],
        "temp_max_celsius": [35.0],
        "temp_min_celsius": [22.0],
        "precipitation_mm": [0.0],
        "precipitation_prob_pct": [5],
        "wind_speed_max_kmh": [25.0],
        "wind_gusts_max_kmh": [40.0],
        "weather_code": [0],
    }


def test_add_categories_adds_all_columns():
    out = add_categories(pd.DataFrame(_clim_row()))
    for col in ["temp_category", "precip_category", "wind_category", "season", "is_weekend"]:
        assert col in out.columns
    assert out.loc[0, "temp_category"] == "Hot"
    assert out.loc[0, "precip_category"] == "Dry"
    assert out.loc[0, "season"] == "Autumn"
    assert out.loc[0, "is_weekend"] == True


def test_build_gold_dataset_full_columns():
    gold = build_gold_dataset(pd.DataFrame(_clim_row()))
    assert len(gold) == 1
    for col in ["temp_category", "risk_score", "risk_level"]:
        assert col in gold.columns
    score, level = compute_risk_score(pd.DataFrame(_clim_row()).iloc[0])
    assert gold.loc[0, "risk_score"] == score
    assert gold.loc[0, "risk_level"] == level
    assert gold.loc[0, "risk_level"] == "LOW"