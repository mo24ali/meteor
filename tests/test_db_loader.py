import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from src.gold.db_loader import upsert_gold_summary


@pytest.fixture
def sqlite_engine():
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(text(
            """
            CREATE TABLE daily_weather_summary (
                city_name VARCHAR NOT NULL,
                latitude NUMERIC,
                longitude NUMERIC,
                country VARCHAR,
                admin_name VARCHAR,
                date DATE NOT NULL,
                temp_max_celsius NUMERIC,
                temp_min_celsius NUMERIC,
                precipitation_mm NUMERIC,
                temp_category VARCHAR,
                precip_category VARCHAR,
                wind_category VARCHAR,
                season VARCHAR,
                is_weekend BOOLEAN,
                risk_score NUMERIC NOT NULL,
                risk_level VARCHAR NOT NULL,
                calculated_at TIMESTAMP,
                UNIQUE (city_name, date)
            )
            """
        ))
    return engine


def _gold_df():
    return pd.DataFrame(
        {
            "city_name": ["Casablanca", "Rabat"],
            "latitude": [33.5992, 34.0209],
            "longitude": [-7.62, -6.8416],
            "country": ["Morocco", "Morocco"],
            "admin_name": ["Casablanca-Settat", "Rabat-Salé-Kénitra"],
            "date": ["2026-09-15", "2026-09-15"],
            "temp_max_celsius": [35.0, 30.0],
            "temp_min_celsius": [22.0, 20.0],
            "precipitation_mm": [0.0, 5.0],
            "temp_category": ["Hot", "Warm"],
            "precip_category": ["Dry", "Light"],
            "wind_category": ["Moderate", "Calm"],
            "season": ["Autumn", "Autumn"],
            "is_weekend": [False, False],
            "risk_score": [15.0, 16.25],
            "risk_level": ["LOW", "LOW"],
        }
    )


def _row_count(engine):
    with engine.connect() as conn:
        return conn.execute(text("SELECT count(*) FROM daily_weather_summary")).scalar()


def test_upsert_gold_summary_inserts_rows(sqlite_engine):
    upsert_gold_summary(_gold_df(), sqlite_engine)
    assert _row_count(sqlite_engine) == 2


def test_upsert_gold_summary_is_idempotent(sqlite_engine):
    upsert_gold_summary(_gold_df(), sqlite_engine)
    upsert_gold_summary(_gold_df(), sqlite_engine)
    assert _row_count(sqlite_engine) == 2


def test_upsert_gold_summary_updates_instead_of_duplicating(sqlite_engine):
    df = _gold_df()
    upsert_gold_summary(df, sqlite_engine)

    updated = df.copy()
    updated.loc[0, "risk_level"] = "EXTREME"
    updated.loc[0, "risk_score"] = 95.0
    upsert_gold_summary(updated, sqlite_engine)

    assert _row_count(sqlite_engine) == 2
    with sqlite_engine.connect() as conn:
        row = conn.execute(
            text("SELECT risk_level, risk_score FROM daily_weather_summary WHERE city_name='Casablanca'")
        ).one()
    assert row.risk_level == "EXTREME"
    assert row.risk_score == 95.0