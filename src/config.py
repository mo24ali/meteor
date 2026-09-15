import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory (meteor root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

class Settings:
    # Weather API Settings
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
    WEATHER_BASE_URL: str = os.getenv("WEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5")

    # PostgreSQL Database Credentials
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "meteor_db")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Medallion Paths
    DATA_DIR: Path = BASE_DIR / "data"
    BRONZE_DIR: Path = DATA_DIR / "bronze"
    SILVER_DIR: Path = DATA_DIR / "silver"
    GOLD_DIR: Path = DATA_DIR / "gold"
    RAW_CITIES_PATH: Path = DATA_DIR / "raw_cities" / "cities.csv"

settings = Settings()