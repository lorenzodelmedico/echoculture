from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from utils.notifications import send_discord_alert

DBT_CMD = "dbt {cmd} --profiles-dir /opt/airflow/dbt --project-dir /opt/airflow/dbt"


def run_ecrantotal_scrape():
    from scrapers.ecrantotal_pipeline import process_ecrantotal

    process_ecrantotal(skip_enrichment=True)


with DAG(
    "scraper_ecrantotal_films",
    schedule_interval="@weekly",
    start_date=datetime(2026, 4, 1),
    catchup=False,
    tags=["culture", "films", "ecrantotal"],
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
        "on_failure_callback": send_discord_alert,
    },
) as dag:

    scrape_films = PythonOperator(
        task_id="scrape_films_ecrantotal",
        python_callable=run_ecrantotal_scrape,
    )

    spark_enrich = BashOperator(
        task_id="spark_enrich_genres",
        bash_command="python /opt/airflow/spark/jobs/wikipedia_genre_enrichment.py",
    )

    dbt_run = BashOperator(
        task_id="dbt_run_films",
        bash_command=DBT_CMD.format(cmd="run --select fct_films+"),
    )

    dbt_test = BashOperator(
        task_id="dbt_test_movies",
        bash_command=DBT_CMD.format(cmd="test --select stg_movies"),
    )

    scrape_films >> spark_enrich >> dbt_run >> dbt_test
