from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from scrapers.archipop_bronze import run_bronze_scraping
from scrapers.archipop_silver import run_silver_transformation_sync
from utils.notifications import send_discord_alert

default_args = {
    "owner": "lorenzo",
    "on_failure_callback": send_discord_alert,
    "depends_on_past": False,
    "start_date": datetime(2026, 4, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "archipop_master_pipeline",
    default_args=default_args,
    description="Pipeline complet : Scraping -> OCR -> LLM -> Postgres -> App",
    schedule_interval="@daily",  # Se lance tous les jours à minuit
    catchup=False,
) as dag:

    # Étape 1 : Récupérer les données brutes
    task_bronze = PythonOperator(
        task_id="fetch_from_web_to_mongo", python_callable=run_bronze_scraping
    )

    # Étape 2 : Transformer et structurer (OCR + LLM)
    task_silver_gold = PythonOperator(
        task_id="llm_structuration_to_postgres",
        python_callable=run_silver_transformation_sync,
    )

    # Définition de l'ordre : Bronze d'abord, puis Silver
    task_bronze >> task_silver_gold
