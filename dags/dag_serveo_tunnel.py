# dags/dag_serveo_tunnel.py
#
# DISABLED — tunnels are managed by start_tunnels.sh on the host machine.
# Running SSH tunnel creation from inside the Airflow container conflicts
# with the host-side tunnels and the container has no SSH keys configured.
# To re-enable: set up SSH keys in the Airflow image and remove start_tunnels.sh.
#
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    "maintenance_serveo_tunnels",
    schedule_interval="@daily",
    start_date=datetime(2026, 4, 1),
    catchup=False,
    is_paused_upon_creation=True,
) as dag:

    # On ouvre les 3 tunnels en une seule commande SSH
    # 2. Backend API (8000)
    # 3. Airflow Logs (8080)
    setup_tunnels = BashOperator(
        task_id="refresh_all_tunnels",
        bash_command="""
        pkill -f serveo.net || true;
        ssh -f -N -o StrictHostKeyChecking=no -o ServerAliveInterval=300 \
        -R echoculture-api-lorenzo:80:echoculture-ui:8000 \
        -R echoculture-airflow-lorenzo:80:airflow-webserver:8080 \
        serveo.net
        """,
    )
