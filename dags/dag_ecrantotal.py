from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from utils.notifications import send_discord_alert


def run_ecrantotal():
    from scrapers.ecrantotal_pipeline import process_ecrantotal

    process_ecrantotal()


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
        python_callable=run_ecrantotal,
    )
