from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.utils.trigger_rule import TriggerRule

from tmdb_pipeline.tasks.GET_GenreMovieList import ingest_genres
from tmdb_pipeline.tasks.GET_MovieList import ingest_movies
from tmdb_pipeline.tasks.GET_MovieDetails import ingest_movie_details
from tmdb_pipeline.tasks.GET_MovieCredits import ingest_movie_credits


@dag(
    dag_id="tmdb_pipeline",
    description="Load TMDB data into Snowflake BRONZE",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["tmdb", "bronze", "genres"],
)
def tmdb_pipeline():

    @task()
    def load_genres():
        ingest_genres()

    @task(retries=1, retry_delay=timedelta(minutes=2))
    def load_movies():
        ingest_movies()

    @task(retries=3, retry_delay=timedelta(minutes=5))
    def load_movie_details():
        ingest_movie_details()

    @task(retries=3, retry_delay=timedelta(minutes=5))
    def load_movie_credits():
        ingest_movie_credits()

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt && dbt run --target prod",
        retries=0,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt && dbt test --target prod",
        trigger_rule=TriggerRule.ALL_DONE,
    )

    [load_genres(), load_movies()] >> load_movie_details() >> load_movie_credits() >> dbt_run >> dbt_test


tmdb_pipeline()
