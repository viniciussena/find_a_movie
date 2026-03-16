import calendar
import json

import pendulum
import requests
from airflow.sdk import Variable

from database_connections.snowflake_connection import get_snowflake_connection

TMDB_BASE_URL = "https://api.themoviedb.org/3"
ENDPOINT = "/discover/movie"
MAX_PAGES = 500


def ingest_movies() -> None:
    now = pendulum.now("UTC")
    year, month = now.year, now.month
    last_day = calendar.monthrange(year, month)[1]
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day:02d}"
    year_month = f"{year}-{month:02d}"

    token = Variable.get("TMDB_API_READ_ACCESS_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json",
    }

    all_movies = []
    page = 1
    hit_limit = False

    while page <= MAX_PAGES:
        response = requests.get(
            f"{TMDB_BASE_URL}{ENDPOINT}",
            headers=headers,
            params={
                "primary_release_date.gte": start_date,
                "primary_release_date.lte": end_date,
                "sort_by": "primary_release_date.desc",
                "language": "en-US",
                "page": page,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])

        if not results:
            break

        all_movies.extend(results)
        total_pages = data.get("total_pages", 1)

        if page >= total_pages:
            break

        if page >= MAX_PAGES:
            hit_limit = True
            print(f"[WARN] Reached {MAX_PAGES}-page API limit for {year_month}. Stopping.")
            break

        page += 1

    print(f"[INFO] Fetched {len(all_movies)} movies for {year_month}")

    if all_movies:
        conn = get_snowflake_connection()
        cur = conn.cursor()
        try:
            cur.execute("USE SCHEMA BRONZE")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS TMDB_MOVIE_RAW (
                    movie_id    INTEGER       NOT NULL,
                    endpoint    VARCHAR(255)  NOT NULL,
                    raw_json    VARIANT       NOT NULL,
                    ingested_at TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
                )
            """)

            insert_values = [
                (movie["id"], ENDPOINT, json.dumps(movie, ensure_ascii=False))
                for movie in all_movies
            ]

            insert_sql = """
                INSERT INTO TMDB_MOVIE_RAW (movie_id, endpoint, raw_json)
                SELECT column1, column2, PARSE_JSON(column3)
                FROM VALUES {}
            """.format(",".join(["(%s, %s, %s)"] * len(insert_values)))

            cur.execute(insert_sql, [v for row in insert_values for v in row])
            conn.commit()
            print(f"[INFO] Loaded {len(all_movies)} movies into BRONZE.TMDB_MOVIE_RAW")
        finally:
            cur.close()
            conn.close()
    else:
        print(f"[INFO] No movies found for {year_month}, skipping insert")

