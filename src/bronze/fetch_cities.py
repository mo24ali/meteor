import pandas as pd
import os

def load_moroccan_cities(csv_path: str= "data/raw_cities/cities.csv") -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Missing cities file at {csv_path}")

    df = pd.read_csv(csv_path)

    required_cols = ['city', 'lat', 'lng']

    df_cities = df[required_cols].copy()

    print(f"Succcessfully loaded")
    return df_cities

if __name__ == "__main__":
    cities = load_moroccan_cities()
    print(cities.head())


