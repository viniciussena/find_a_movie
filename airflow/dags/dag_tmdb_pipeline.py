from datetime import datetime

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.utils.trigger_rule import TriggerRule

from tmdb_pipeline.tasks.GET_GenreMovieList import ingest_genres


@dag(
    dag_id="tmdb_pipeline",
    description="Load TMDB data into Snowflake BRONZE",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["tmdb", "bronze", "genres"],
)
def tmdb_genres_pipeline():

    @task()
    def load_genres():
        ingest_genres()

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

    load_genres() >> dbt_run >> dbt_test


tmdb_genres_pipeline()