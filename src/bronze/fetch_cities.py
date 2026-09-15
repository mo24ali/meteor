import os

import pandas as pd

REQUIRED_COLUMNS = ["city", "lat", "lng"]


def load_moroccan_cities(csv_path: str = "data/raw_cities/cities.csv") -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Missing cities file at {csv_path}")

    df = pd.read_csv(csv_path)

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Cities file is missing required columns: {missing_cols}. "
            f"Found: {list(df.columns)}"
        )

    df_cities = df[REQUIRED_COLUMNS].copy()
    df_cities = df_cities.dropna(subset=REQUIRED_COLUMNS)

    print(f"Successfully loaded {len(df_cities)} cities from {csv_path}")
    return df_cities


if __name__ == "__main__":
    print(load_moroccan_cities().head())