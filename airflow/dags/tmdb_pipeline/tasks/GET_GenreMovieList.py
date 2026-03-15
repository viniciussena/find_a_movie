import json
import requests
from airflow.models import Variable

from database_connections.snowflake_connection import get_snowflake_connection

TMDB_BASE_URL = "https://api.themoviedb.org/3"


def ingest_genres() -> None:
    token = Variable.get("TMDB_API_READ_ACCESS_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json",
    }

    response = requests.get(
        f"{TMDB_BASE_URL}/genre/movie/list",
        headers=headers,
        params={"language": "en"},
        timeout=30,
    )
    response.raise_for_status()
    response_json = response.json()
    genres = response_json["genres"]
    raw_json = json.dumps(response_json, ensure_ascii=False)
    print(f"Fetched {len(genres)} genres from TMDB")

    conn = get_snowflake_connection()
    cur = conn.cursor()
    try:
        cur.execute("USE SCHEMA BRONZE")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS TMDB_GENRE_RAW (
                genre_id    INTEGER       NOT NULL,
                genre_name  VARCHAR(100)  NOT NULL,
                endpoint    VARCHAR(255)  NOT NULL,
                raw_json    VARIANT       NOT NULL,
                ingested_at TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
            )
        """)
        insert_values = [(g["id"], g["name"], "/genre/movie/list", raw_json) for g in genres]

        insert_sql = """
            INSERT INTO TMDB_GENRE_RAW (genre_id, genre_name, endpoint, raw_json)
            SELECT column1, column2, column3, PARSE_JSON(column4)
            FROM VALUES {}
        """.format(",".join(["(%s, %s, %s, %s)"] * len(insert_values)))

        cur.execute(insert_sql, [v for row in insert_values for v in row])
        conn.commit()
        print(f"Loaded {len(genres)} genres into BRONZE.TMDB_GENRE_RAW")
    finally:
        cur.close()
        conn.close()
