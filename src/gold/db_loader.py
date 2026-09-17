import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import MetaData, Table, create_engine, text

from src.gold.risk_score import build_gold_dataset
from src.utils.db_connection import get_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SCHEMA_SQL = BASE_DIR / "sql" / "schema.sql"

GOLD_INSERT_COLUMNS = [
    "city_name", "latitude", "longitude", "country", "admin_name", "date",
    "temp_max_celsius", "temp_min_celsius", "precipitation_mm",
    "temp_category", "precip_category", "wind_category",
    "season", "is_weekend", "risk_score", "risk_level",
]


def ensure_schema(engine=None) -> None:
    engine = engine or get_engine()
    with engine.begin() as conn:
        conn.execute(text(SCHEMA_SQL.read_text(encoding="utf-8")))
    logger.info("Database schema ensured")


def _gold_table(engine):
    schema = None if engine.dialect.name == "sqlite" else "gold"
    return Table(
        "daily_weather_summary",
        MetaData(),
        autoload_with=engine,
        schema=schema,
    )


def upsert_gold_summary(df: pd.DataFrame, engine=None) -> int:
    engine = engine or get_engine()
    table = _gold_table(engine)

    rows = (
        df[GOLD_INSERT_COLUMNS]
        .assign(date=pd.to_datetime(df["date"]))
        .to_dict("records")
    )

    if engine.dialect.name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    else:
        from sqlalchemy.dialects.postgresql import insert

    insert_stmt = insert(table).values(rows)
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["city_name", "date"],
        set_={col: insert_stmt.excluded[col] for col in GOLD_INSERT_COLUMNS},
    )

    with engine.begin() as conn:
        conn.execute(upsert_stmt)

    logger.info("Upserted %d rows into gold.daily_weather_summary", len(rows))
    return len(rows)


def load_gold(csv_path: str, engine=None, skip_schema: bool = False) -> int:
    engine = engine or get_engine()
    silver = pd.read_csv(csv_path)
    gold = build_gold_dataset(silver)

    if not skip_schema:
        ensure_schema(engine)

    return upsert_gold_summary(gold, engine)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gold layer: load enriched silver weather into PostgreSQL."
    )
    parser.add_argument(
        "--csv", default="data/silver/weather_enriched.csv", help="Silver input CSV"
    )
    parser.add_argument(
        "--skip-schema", action="store_true", help="Skip DDL execution (schema already present)"
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    load_gold(args.csv, skip_schema=args.skip_schema)