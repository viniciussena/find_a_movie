# 🎬 Find a Movie

Find your next movie through data.

**Find a Movie** is a movie discovery and analytics platform that builds a curated catalog of films using public movie data.
The platform organizes titles, genres, ratings, and trends into a clean analytical model that powers exploration and interactive dashboards.

This project demonstrates how raw public data can be transformed into a structured data product for discovery, analysis, and insights.

---

## 🚀 Features

- Curated movie catalog from the TMDB API
- Exploration by genre, popularity, rating, and release year
- Analytical data model for insights (Bronze → Silver → Gold)
- Automated data pipeline orchestrated by Apache Airflow
- Interactive dashboard for movie discovery

---

## 🏗 Architecture

```
TMDB API
    │
    ▼
Apache Airflow 3.0.1
(Orchestration — CeleryExecutor + Redis)
    │
    ▼
Snowflake — DB_FIND_A_MOVIE
    ├── BRONZE   → Raw ingested data
    ├── SILVER   → Cleaned and conformed data
    └── GOLD     → Analytics-ready tables
    │
    ▼
dbt (Data Transformations)
    │
    ▼
BI Dashboard
```

---

## 🧠 How It Works

1. **Data Ingestion** — Airflow DAGs extract movie data from the TMDB API
2. **Bronze Layer** — Raw API responses stored with minimal processing in Snowflake
3. **Silver Layer** — Data standardized, deduplicated, and normalized via dbt
4. **Gold Layer** — Dimensional models power analytics and dashboards
5. **Visualization** — Dashboards allow users to explore the movie catalog

---

## 🗂 Project Structure

```
find_a_movie/
├── airflow/
│   ├── config/
│   │   └── airflow.cfg
│   └── dags/
│       └── database_connections/
│           ├── snowflake_connection.py
│           └── snowflake_utils.py
├── dbt/
│   ├── models/
│   │   ├── bronze/
│   │   ├── silver/
│   │   └── gold/
│   ├── macros/
│   ├── dbt_project.yml
│   ├── packages.yml
│   └── profiles.yml.example
├── docs/
│   └── TMDB Api Reference.md
├── secrets/              # SSH keys — not committed
├── docker-compose.yaml
├── Dockerfile
├── requirements.txt
├── .env.example
└── CLAUDE.md
```

---

## ⚙️ Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/viniciussena/find_a_movie.git
cd find_a_movie
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Fill in AIRFLOW_PROJ_DIR and SNOWFLAKE_PRIVATE_KEY_PATH
```

### 3. Configure dbt profile

```bash
cp dbt/profiles.yml.example dbt/profiles.yml
# Fill in your Snowflake credentials
```

### 4. Add Snowflake SSH key

Place your private key at the path defined in `.env` under `SNOWFLAKE_PRIVATE_KEY_PATH`.

### 5. Set up TMDB API access

1. Create a free account at [themoviedb.org](https://www.themoviedb.org/signup)
2. Go to **Settings → API → Request an API Key → Developer**
3. Fill in app name (`find_a_movie`), URL (`http://localhost`), type (`Desktop Application`)
4. Copy the **API Read Access Token** (the long `eyJ...` JWT — not the short API Key)

### 6. Start the stack

```bash
docker-compose up --build -d
```

Airflow UI will be available at [http://localhost:8080](http://localhost:8080) (default: `airflow` / `airflow`).

### 7. Add the TMDB token to Airflow

After the stack is up:
- Go to **Admin → Variables → `+`**
- **Key:** `TMDB_API_READ_ACCESS_TOKEN`
- **Value:** paste the full `eyJ...` token from TMDB

---

## 📊 Example Insights

- What are the most popular movies right now?
- How do ratings vary across genres?
- What genres dominate each release year?
- Which movies have the highest audience ratings?
- How does popularity evolve over time?

---

## 🎯 Project Goals

- Design a robust ingestion pipeline from a public API
- Structure layered data models (medallion architecture)
- Enable analytical exploration through clean data products
- Deliver insights through dashboards

---

## 📚 Educational Purpose

This repository is a practical learning project demonstrating modern data pipeline architecture and analytics engineering concepts using industry-standard tools (Airflow, dbt, Snowflake).

---

## 📄 License

MIT License
