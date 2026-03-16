from datetime import datetime, timedelta

from airflow.decorators import dag, task

from tmdb_pipeline.tasks.GET_MovieListFULL import ingest_movies_full


@dag(
    dag_id="tmdb_full_load_movies",
    description="One-time full historical load of TMDB movies (2026-02 back to 1874-01)",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["tmdb", "bronze", "movies", "full_load"],
)
def tmdb_full_load():

    @task(retries=1, retry_delay=timedelta(minutes=2))
    def load_movies_full():
        ingest_movies_full()

    load_movies_full()


tmdb_full_load()
