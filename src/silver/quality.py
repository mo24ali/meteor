import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

REQUIRED_COLUMNS = [
    "city_name", "latitude", "longitude", "date",
    "temp_max_celsius", "temp_min_celsius", "precipitation_mm",
    "precipitation_prob_pct", "wind_speed_max_kmh", "wind_gusts_max_kmh",
    "weather_code",
]

WMO_CODES = {
    0, 1, 2, 3, 45, 48, 51, 53, 55, 56, 57, 61, 63, 65, 66, 67,
    71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99,
}

NOT_NULL_COLUMNS = [
    "city_name", "date", "temp_max_celsius", "temp_min_celsius",
    "precipitation_mm", "wind_speed_max_kmh", "weather_code",
]


def _issue(check: str, count: int, detail: str) -> dict:
    return {"check": check, "issues": int(count), "detail": detail}


def run_quality_checks(df: pd.DataFrame) -> pd.DataFrame:
    issues = []
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        issues.append(_issue(
            "required_columns", len(missing_cols), f"missing: {missing_cols}"
        ))
        return pd.DataFrame(issues)

    nulls = df[NOT_NULL_COLUMNS].isna().sum()
    for col, count in nulls.items():
        if count:
            issues.append(_issue("no_null", count, f"column '{col}' has NULLs"))

    bad_minmax = df[df["temp_min_celsius"] > df["temp_max_celsius"]]
    if not bad_minmax.empty:
        issues.append(_issue("temp_min_le_max", len(bad_minmax), "temp_min > temp_max"))

    warm = df[df["temp_max_celsius"] > 60]
    if not warm.empty:
        issues.append(_issue("temp_range", len(warm), "temp_max > 60 C"))

    cold = df[df["temp_min_celsius"] < -20]
    if not cold.empty:
        issues.append(_issue("temp_range", len(cold), "temp_min < -20 C"))

    neg_precip = df[df["precipitation_mm"] < 0]
    if not neg_precip.empty:
        issues.append(_issue("precip_ge_0", len(neg_precip), "negative precipitation_mm"))

    prob = df[~df["precipitation_prob_pct"].between(0, 100)]
    if not prob.empty:
        issues.append(_issue("prob_range", len(prob), "precipitation_prob_pct outside 0-100"))

    neg_wind = df[df["wind_speed_max_kmh"] < 0]
    if not neg_wind.empty:
        issues.append(_issue("wind_ge_0", len(neg_wind), "negative wind_speed_max_kmh"))

    lat = df[~df["latitude"].between(-90, 90)]
    if not lat.empty:
        issues.append(_issue("lat_range", len(lat), "latitude outside -90..90"))

    lng = df[~df["longitude"].between(-180, 180)]
    if not lng.empty:
        issues.append(_issue("lng_range", len(lng), "longitude outside -180..180"))

    bad_code = df[~df["weather_code"].isin(WMO_CODES)]
    if not bad_code.empty:
        issues.append(_issue(
            "wmo_code_valid", len(bad_code),
            f"codes outside known WMO set: {bad_code['weather_code'].unique().tolist()}",
        ))

    dupes = df.duplicated(subset=["city_name", "date"], keep=False)
    if dupes.any():
        issues.append(_issue("city_date_unique", int(dupes.sum()), "duplicate city_name+date rows"))

    return pd.DataFrame(issues, columns=["check", "issues", "detail"])