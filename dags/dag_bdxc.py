from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from scrapers.bdxc_pipeline import process_bdxc
import sys

sys.path.append("/opt/airflow")

default_args = {
    "owner": "lorenzo",
    "start_date": datetime(2026, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "scraper_bdxc_mongodb_to_pg",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
    tags=["culture", "bdxc", "api"],
) as dag:

    run_pipeline = PythonOperator(
        task_id="process_bdxc_full",
        python_callable=process_bdxc,
    )
