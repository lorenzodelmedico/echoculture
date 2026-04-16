import sys
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from utils.notifications import send_discord_alert

sys.path.append("/opt/airflow")

DBT_CMD = "dbt {cmd} --profiles-dir /opt/airflow/dbt --project-dir /opt/airflow/dbt"

default_args = {
    "owner": "lorenzo",
    "start_date": datetime(2026, 4, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": send_discord_alert,
}


def run_spectacles():
    from scrapers.bdxc_pipeline import process_bdxc

    process_bdxc(category="spectacles")


with DAG(
    "scraper_bdxc_spectacles",
    default_args=default_args,
    schedule_interval="@weekly",
    catchup=False,
    tags=["culture", "bdxc", "spectacles"],
) as dag:

    run_pipeline = PythonOperator(
        task_id="process_bdxc_spectacles",
        python_callable=run_spectacles,
    )

    dbt_run = BashOperator(
        task_id="dbt_run_spectacles",
        bash_command=DBT_CMD.format(cmd="run --select fct_spectacles+"),
    )

    dbt_test = BashOperator(
        task_id="dbt_test_events",
        bash_command=DBT_CMD.format(cmd="test --select stg_events"),
    )

    run_pipeline >> dbt_run >> dbt_test
