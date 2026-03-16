import calendar
import json

import pendulum
import requests
from airflow.sdk import Variable

from database_connections.snowflake_connection import get_snowflake_connection

TMDB_BASE_URL = "https://api.themoviedb.org/3"
ENDPOINT = "/discover/movie"
MAX_PAGES = 500
END_YEAR_MONTH = (1874, 1)


def _fetch_month(headers: dict, year: int, month: int) -> list:
    last_day = calendar.monthrange(year, month)[1]
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day:02d}"
    year_month = f"{year}-{month:02d}"

    all_movies = []
    page = 1

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
            print(f"[WARN] Reached {MAX_PAGES}-page API limit for {year_month}. Moving on.")
            break

        page += 1

    return all_movies


def _insert_movies(cur, movies: list) -> None:
    insert_values = [
        (movie["id"], ENDPOINT, json.dumps(movie, ensure_ascii=False))
        for movie in movies
    ]
    insert_sql = """
        INSERT INTO TMDB_MOVIE_RAW (movie_id, endpoint, raw_json)
        SELECT column1, column2, PARSE_JSON(column3)
        FROM VALUES {}
    """.format(",".join(["(%s, %s, %s)"] * len(insert_values)))
    cur.execute(insert_sql, [v for row in insert_values for v in row])


def ingest_movies_full() -> None:
    token = Variable.get("TMDB_API_READ_ACCESS_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json",
    }

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

        now = pendulum.now("UTC")
        current = pendulum.datetime(now.year, now.month, 1)
        end = pendulum.datetime(*END_YEAR_MONTH, 1)
        total_inserted = 0

        while current >= end:
            year, month = current.year, current.month
            year_month = current.format("YYYY-MM")

            movies = _fetch_month(headers, year, month)

            if movies:
                _insert_movies(cur, movies)
                conn.commit()
                total_inserted += len(movies)
                print(f"[INFO] {year_month}: inserted {len(movies)} movies (total so far: {total_inserted})")
            else:
                print(f"[INFO] {year_month}: no movies found, skipping")

            current = current.subtract(months=1)

        print(f"[INFO] Full load complete. Total movies inserted: {total_inserted}")

    finally:
        cur.close()
        conn.close()
