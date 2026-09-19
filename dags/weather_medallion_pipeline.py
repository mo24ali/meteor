from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

DEFAULT_ARGS = {
    "owner": "meteor",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(hours=1),
}

PIPELINE_STEPS = [
    {
        "task_id": "bronze_extract_weather",
        "description": "Extract daily weather forecasts from the Open-Meteo API for all Moroccan cities.",
        "command": "python -m src.bronze.fetch_weather --resume",
    },
    {
        "task_id": "silver_clean_weather",
        "description": "Clean and standardize bronze snapshots into a tidy silver dataset.",
        "command": "python -m src.silver.clean_weather",
    },
    {
        "task_id": "silver_enrich_cities",
        "description": "Enrich silver weather with city metadata (country, admin area).",
        "command": "python -m src.silver.join_data",
    },
    {
        "task_id": "gold_risk_features",
        "description": "Feature engineering: temperature/precip/wind categories, season and risk score.",
        "command": "python -m src.gold.risk_score",
    },
    {
        "task_id": "gold_load_postgres",
        "description": "Upsert the gold summary into PostgreSQL (refreshes the dashboard data).",
        "command": "python -m src.gold.db_loader",
    },
]

with DAG(
    dag_id="weather_medallion_pipeline",
    default_args=DEFAULT_ARGS,
    description=(
        "Medallion pipeline: extract weather forecasts, clean/enrich, engineer "
        "risk features and load the gold summary into PostgreSQL."
    ),
    schedule_interval="@daily",
    start_date=datetime(2026, 9, 18),
    catchup=False,
    tags=["weather", "medallion", "morocco"],
) as dag:

    check_cities = BashOperator(
        task_id="check_cities_file",
        doc_md="Guard task: the cities catalog must exist before ingesting weather.",
        bash_command="test -f /opt/airflow/data/raw_cities/cities.csv",
    )

    steps = []
    for step in PIPELINE_STEPS:
        steps.append(
            BashOperator(
                task_id=step["task_id"],
                doc_md=step["description"],
                bash_command=f"cd /opt/airflow && {step['command']}",
            )
        )

    check_cities >> steps[0]
    for idx in range(len(steps) - 1):
        steps[idx] >> steps[idx + 1]