from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "lorenzo",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "maintenance_cleanup_tmp",
    default_args=default_args,
    description="Nettoyage hebdomadaire des fichiers temporaires",
    schedule_interval="@weekly",  # Une fois par semaine (Dimanche minuit)
    start_date=datetime(2026, 4, 1),
    catchup=False,
) as dag:

    # Commande pour supprimer les fichiers de plus de 7 jours dans /tmp
    clean_tmp = BashOperator(
        task_id="delete_old_tmp_files",
        bash_command="find /tmp -type f -mtime +7 -delete",
    )
