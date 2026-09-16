import pandas as pd
import pytest

from src.silver.join_data import enrich_weather_with_cities, load_city_metadata

META_CSV = "city,lat,lng,country,admin_name\n" \
           "Casablanca,33.5992,-7.62,Morocco,Casablanca-Settat\n" \
           "Rabat,34.0209,-6.8416,Morocco,Rabat-Salé-Kénitra\n"

WEATHER_CSV = "city_name,date,temp_max_celsius\n" \
              "Casablanca,2026-09-15,28.0\n" \
              "Rabat,2026-09-15,26.0\n"


def test_load_city_metadata_keeps_meta_columns(tmp_path):
    cities_path = tmp_path / "cities.csv"
    cities_path.write_text(META_CSV, encoding="utf-8")
    df = load_city_metadata(str(cities_path))
    assert df.columns.tolist() == ["city", "country", "admin_name"]
    assert len(df) == 2


def test_load_city_metadata_raises_on_missing_columns(tmp_path):
    cities_path = tmp_path / "cities.csv"
    cities_path.write_text("city\nCasablanca\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required columns"):
        load_city_metadata(str(cities_path))