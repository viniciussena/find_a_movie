# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A data pipeline for a movie recommendation/analytics system that fetches data from the TMDB API, loads it into Snowflake, and transforms it through a medallion architecture (Bronze → Silver → Gold) using dbt.

The project is in its initial setup phase — the Airflow stack is running but no DAGs have been created yet.

## Repository

https://github.com/viniciussena/find_a_movie

## Development Commands

### Docker-based development (primary workflow)
```bash
# First time / after dependency changes
docker-compose up --build -d

# Start (after already built)
docker-compose up -d

# View logs
docker-compose logs -f airflow-apiserver
docker-compose logs -f airflow-scheduler

# Stop services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### dbt commands (local — run inside c:\viniciusfsena\find_a_movie\dbt)
```bash
# Install packages
dbt deps

# Run all models
dbt run

# Run a specific model
dbt run --select <model_name>

# Run models in a layer
dbt run --select bronze.*
dbt run --select silver.*
dbt run --select gold.*

# Run tests
dbt test

# Check compilation without executing
dbt compile
```

### Airflow (inside container)
```bash
# Shell into scheduler
docker-compose exec airflow-scheduler bash

# Trigger DAG manually
airflow dags trigger <dag_id>

# List DAG tasks
airflow tasks list <dag_id>

# Test a single task
airflow tasks test <dag_id> <task_id> <execution_date>
```

## Architecture

### Stack
- **Orchestration:** Apache Airflow 3.0.1 (CeleryExecutor with Redis broker)
- **Data Warehouse:** Snowflake (`DB_FIND_A_MOVIE` database)
- **Transformation:** dbt-core with dbt-snowflake adapter
- **Airflow-dbt integration:** astronomer-cosmos
- **Metadata DB:** PostgreSQL 13 (persisted via Docker volume `find_a_movie_postgres-db-volume`)

### Key Directories
- `airflow/dags/database_connections/` — Snowflake connection utilities (`snowflake_connection.py`, `snowflake_utils.py`)
- `dbt/models/bronze/` — Staging models (raw data)
- `dbt/models/silver/` — Cleaned/transformed models
- `dbt/models/gold/` — Business-facing analytics tables
- `dbt/macros/` — Custom Jinja2 macros (includes `generate_schema_name.sql`)
- `secrets/` — SSH key pair for Snowflake auth (not committed)
- `docs/` — API reference documentation

### Snowflake Layout
```
DB_FIND_A_MOVIE database
├── BRONZE_PMS   — Raw ingested data
├── BRONZE_BC    — Raw ingested data
├── SILVER       — Cleaned and conformed data
├── GOLD         — Analytics-ready tables
└── MONITORING   — Pipeline run logs
```

### Snowflake Credentials
- **Account:** `VIBIZOV-IS28444`
- **User:** `DATA_PIPELINE_USER`
- **Warehouse:** `DW_FIND_A_MOVIE`
- **Role:** `DATA_PIPELINE_ROLE`
- **Auth:** SSH key pair — path read from `SNOWFLAKE_PRIVATE_KEY_PATH` env var

### dbt Package Dependencies
- `dbt_utils` — General SQL utilities
- `dbt_expectations` — Data quality assertions

## External APIs

### TMDB API
Documentation is at `docs/TMDB Api Reference.md`. Read this file whenever working with
TMDB API integrations, endpoints, authentication, or data models.

## Environment Setup

Template files for setup (copy and fill in credentials):
- `.env.example` → `.env`
- `dbt/profiles.yml.example` → `dbt/profiles.yml`

Copy `.env.example` to `.env` before running Docker:
```bash
cp .env.example .env
```

The `.env` file must contain:
```
AIRFLOW_UID=50000
AIRFLOW_PROJ_DIR=<absolute path to project root>
SNOWFLAKE_PRIVATE_KEY_PATH=/home/airflow/.ssh/snowflake_find_a_movie_rsa_key.p8
```

Snowflake authentication uses SSH key pairs stored in `secrets/` (not committed).
The key is volume-mounted into the container at `/home/airflow/.ssh/`.

### dbt Profiles
`dbt/profiles.yml` has two profiles (both named `find_a_movie`):
- **Windows (active):** Uses local key path `C:\Users\vinic\.ssh\snowflake_find_a_movie_rsa_key.p8`
- **Docker (commented out):** Uses container path `/home/airflow/.ssh/snowflake_find_a_movie_rsa_key.p8` — uncomment when running dbt inside Docker

### Airflow UI
- URL: `http://localhost:8080`
- Default credentials: `airflow` / `airflow`
