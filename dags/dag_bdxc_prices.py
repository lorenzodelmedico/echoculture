import sys
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from scrapers.bdxc_prices_pipeline import process_bdxc_prices
from utils.notifications import send_discord_alert

sys.path.append("/opt/airflow")

default_args = {
    "owner": "lorenzo",
    "start_date": datetime(2026, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": send_discord_alert,
}

with DAG(
    "scraper_bdxc_prices",
    default_args=default_args,
    schedule_interval="@weekly",
    catchup=False,
    tags=["culture", "bdxc", "prices"],
) as dag:

    run_pipeline = PythonOperator(
        task_id="process_bdxc_prices",
        python_callable=process_bdxc_prices,
    )
