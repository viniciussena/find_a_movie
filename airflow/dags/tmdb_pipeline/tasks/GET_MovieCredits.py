import json
import time

import requests
from airflow.sdk import Variable

from database_connections.snowflake_connection import get_snowflake_connection

TMDB_BASE_URL = "https://api.themoviedb.org/3"
ENDPOINT_TEMPLATE = "/movie/{movie_id}/credits"
BATCH_SIZE = 500
THROTTLE_SECONDS = 0.03  # ~33 req/s, safely below TMDB's ~40 req/s limit
LOG_INTERVAL = 1000


def _fetch_credits(session: requests.Session, movie_id: int, headers: dict) -> dict | None:
    url = f"{TMDB_BASE_URL}/movie/{movie_id}/credits"
    delay = 1.0
    for attempt in range(6):
        resp = session.get(url, headers=headers, params={"language": "en-US"}, timeout=30)
        if resp.status_code == 429:
            time.sleep(delay)
            delay = min(delay * 2, 60)
            continue
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    return None


def _insert_batch(cur, batch: list[tuple]) -> None:
    insert_sql = """
        INSERT INTO TMDB_MOVIE_CREDITS_RAW (movie_id, endpoint, raw_json)
        SELECT column1, column2, PARSE_JSON(column3)
        FROM VALUES {}
    """.format(",".join(["(%s, %s, %s)"] * len(batch)))
    cur.execute(insert_sql, [v for row in batch for v in row])


def ingest_movie_credits() -> None:
    token = Variable.get("TMDB_API_READ_ACCESS_TOKEN")
    headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}

    conn = get_snowflake_connection()
    cur = conn.cursor()
    try:
        cur.execute("USE SCHEMA BRONZE")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS TMDB_MOVIE_CREDITS_RAW (
                movie_id    INTEGER       NOT NULL,
                endpoint    VARCHAR(255)  NOT NULL,
                raw_json    VARIANT       NOT NULL,
                ingested_at TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
            )
        """)

        # Only fetch credits for movies that already have details ingested
        cur.execute("""
            SELECT DISTINCT movie_id
            FROM TMDB_MOVIE_DETAILS_RAW
            WHERE movie_id NOT IN (SELECT DISTINCT movie_id FROM TMDB_MOVIE_CREDITS_RAW)
            ORDER BY movie_id
        """)
        movie_ids = [row[0] for row in cur.fetchall()]
        total = len(movie_ids)
        print(f"[INFO] Credits: {total} movies to process")

        if not movie_ids:
            print("[INFO] No new movies to fetch credits for.")
            return

        session = requests.Session()
        batch: list[tuple] = []
        processed = 0

        for movie_id in movie_ids:
            data = _fetch_credits(session, movie_id, headers)
            time.sleep(THROTTLE_SECONDS)

            if data is None:
                continue

            endpoint = ENDPOINT_TEMPLATE.format(movie_id=movie_id)
            batch.append((movie_id, endpoint, json.dumps(data, ensure_ascii=False)))

            if len(batch) >= BATCH_SIZE:
                _insert_batch(cur, batch)
                conn.commit()
                batch = []

            processed += 1
            if processed % LOG_INTERVAL == 0:
                print(f"[INFO] Credits: processed {processed}/{total}")

        if batch:
            _insert_batch(cur, batch)
            conn.commit()

        print(f"[INFO] Credits: done. Inserted {processed} records into BRONZE.TMDB_MOVIE_CREDITS_RAW")
    finally:
        cur.close()
        conn.close()
