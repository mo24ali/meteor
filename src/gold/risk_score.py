import argparse
import pathlib

import numpy as np
import pandas as pd

RISK_WEIGHTS = {"temp": 0.30, "precip": 0.30, "wind": 0.20, "wmo": 0.20}

RISK_LEVELS = [
    (0.0, 35.0, "LOW"),
    (35.0, 55.0, "MODERATE"),
    (55.0, 75.0, "HIGH"),
    (75.0, 101.0, "EXTREME"),
]

WMO_SEVERITY = {
    0: 0,
    1: 10, 2: 10, 3: 10,
    45: 30, 48: 30,
    51: 50, 53: 55, 55: 60,
    56: 55, 57: 60,
    61: 60, 63: 70, 65: 80,
    66: 70, 67: 80,
    71: 40, 73: 50, 75: 65, 77: 70,
    80: 70, 81: 75, 82: 85,
    85: 80, 86: 90,
    95: 90, 96: 100, 99: 100,
}

CATEGORY_COLUMNS = [
    "temp_category", "precip_category", "wind_category",
    "season", "is_weekend", "risk_score", "risk_level",
]

GOLD_COLUMNS = [
    "city_name", "latitude", "longitude", "country", "admin_name", "date",
    "temp_max_celsius", "temp_min_celsius", "precipitation_mm",
    "temp_category", "precip_category", "wind_category",
    "season", "is_weekend", "risk_score", "risk_level",
]


def temp_score(temp_max: float) -> float:
    if temp_max <= 30:
        return 0.0
    if temp_max >= 40:
        return 100.0
    return round((temp_max - 30) / 10.0 * 100, 2)


def precip_score(precip_mm: float) -> float:
    if precip_mm < 1:
        return 0.0
    return round(min(precip_mm / 50.0 * 100, 100), 2)


def wind_score(speed_kmh: float) -> float:
    if speed_kmh < 20:
        return 0.0
    return round(min((speed_kmh - 20) / 80.0 * 100, 100), 2)


def wmo_severity(code: int) -> float:
    return float(WMO_SEVERITY.get(code, 50))


def risk_level(score: float) -> str:
    for _, upper, level in RISK_LEVELS:
        if score < upper:
            return level
    return RISK_LEVELS[-1][2]


def compute_risk_score(row) -> tuple:
    score = round(
        RISK_WEIGHTS["temp"] * temp_score(row["temp_max_celsius"])
        + RISK_WEIGHTS["precip"] * precip_score(row["precipitation_mm"])
        + RISK_WEIGHTS["wind"] * wind_score(row["wind_speed_max_kmh"])
        + RISK_WEIGHTS["wmo"] * wmo_severity(row["weather_code"]),
        2,
    )
    return score, risk_level(score)


def add_categories(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"])

    out["temp_category"] = pd.cut(
        out["temp_max_celsius"],
        bins=[-np.inf, 25, 32, 38, np.inf],
        labels=["Mild", "Warm", "Hot", "Extreme"],
    ).astype(str)

    out["precip_category"] = pd.cut(
        out["precipitation_mm"],
        bins=[-np.inf, 1, 10, 30, np.inf],
        labels=["Dry", "Light", "Moderate", "Heavy"],
    ).astype(str)

    out["wind_category"] = pd.cut(
        out["wind_speed_max_kmh"],
        bins=[-np.inf, 20, 40, 60, np.inf],
        labels=["Calm", "Moderate", "Strong", "Extreme"],
    ).astype(str)

    month = out["date"].dt.month
    out["season"] = np.select(
        condlist=[
            month.isin([12, 1, 2]),
            month.isin([3, 4, 5]),
            month.isin([6, 7, 8]),
        ],
        choicelist=["Winter", "Spring", "Summer"],
        default="Autumn",
    )

    out["is_weekend"] = out["date"].dt.weekday >= 5

    return out


def build_gold_dataset(silver_df: pd.DataFrame) -> pd.DataFrame:
    df = add_categories(silver_df)
    df[["risk_score", "risk_level"]] = df.apply(
        lambda r: compute_risk_score(r),
        axis=1,
        result_type="expand",
    )
    return df.reindex(columns=GOLD_COLUMNS)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gold layer: build categories and risk scores from silver weather."
    )
    parser.add_argument("--silver-csv", default="data/silver/weather_enriched.csv")
    parser.add_argument("--output-csv", default="data/gold/daily_weather_summary.csv")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    silver = pd.read_csv(args.silver_csv)
    gold = build_gold_dataset(silver)
    pathlib.Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    gold.to_csv(args.output_csv, index=False)
    print(f"Gold dataset written to {args.output_csv}: {len(gold)} rows")