#!/bin/bash
# Create a dedicated database for Airflow metadata so it stays separate from meteor_db.
set -e

psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE airflow_meta'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow_meta')\gexec
EOSQL