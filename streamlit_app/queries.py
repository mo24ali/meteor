import pandas as pd
import streamlit as st
from sqlalchemy import text

from src.utils.db_connection import get_engine

RISK_COLORS = {
    "LOW": "#2E7D32",
    "MODERATE": "#F57C00",
    "HIGH": "#D32F2F",
    "EXTREME": "#6A1B9A",
}


@st.cache_data(ttl=600, show_spinner="Loading gold layer…")
def load_gold() -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(
            text("SELECT * FROM gold.daily_weather_summary ORDER BY city_name, date"),
            conn,
        )
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(ttl=600, show_spinner="Loading silver layer…")
def load_silver() -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM silver.weather ORDER BY city_name, date"), conn)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


def risk_color(level) -> str:
    return RISK_COLORS.get(str(level).upper(), "#9E9E9E")


def latest_per_city(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[df.groupby("city_name")["date"].idxmax()].copy()