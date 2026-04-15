from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from scrapers.bdxc_pipeline import process_bdxc
from utils.notifications import send_discord_alert
import sys

sys.path.append("/opt/airflow")

DBT_CMD = "dbt {cmd} --profiles-dir /opt/airflow/dbt --project-dir /opt/airflow/dbt"

default_args = {
    "owner": "lorenzo",
    "start_date": datetime(2026, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": send_discord_alert,
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

    dbt_run = BashOperator(
        task_id="dbt_run_concerts",
        bash_command=DBT_CMD.format(cmd="run --select fct_concerts+"),
    )

    dbt_test = BashOperator(
        task_id="dbt_test_events",
        bash_command=DBT_CMD.format(cmd="test --select stg_events"),
    )

    run_pipeline >> dbt_run >> dbt_test
