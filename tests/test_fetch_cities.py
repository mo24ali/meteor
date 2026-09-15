import os

import pandas as pd
import pytest

from src.bronze.fetch_cities import load_moroccan_cities


@pytest.fixture
def cities_csv(tmp_path):
    df = pd.DataFrame(
        {
            "city": ["Casablanca", "Rabat"],
            "lat": [33.5992, 34.0209],
            "lng": [-7.62, -6.8416],
            "population": [3950000, 577827],
        }
    )
    path = tmp_path / "cities.csv"
    df.to_csv(path, index=False)
    return str(path)


def test_load_moroccan_cities_returns_required_columns(cities_csv):
    df = load_moroccan_cities(cities_csv)
    assert list(df.columns) == ["city", "lat", "lng"]
    assert len(df) == 2


def test_load_moroccan_cities_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_moroccan_cities("/nonexistent/cities.csv")


def test_load_moroccan_cities_missing_columns_raises(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("city\nCasablanca\n")

    with pytest.raises(ValueError, match="missing required columns"):
        load_moroccan_cities(str(path))


def test_load_moroccan_cities_dropna(tmp_path):
    path = tmp_path / "na.csv"
    path.write_text("city,lat,lng\nCasablanca,33.6,-7.6\nRabat,,\n")

    df = load_moroccan_cities(str(path))
    assert len(df) == 1