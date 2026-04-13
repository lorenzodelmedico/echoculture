import requests
import os


def send_discord_alert(context):
    ti = context.get("task_instance")
    base_url = os.getenv("AIRFLOW_PUBLIC_URL", "http://localhost:8080")
    log_url = ti.log_url.replace("http://localhost:8080", base_url)

    payload = {
        "content": "🚨 **ALERTE ÉCHEC PIPELINE**",
        "embeds": [
            {
                "title": f"DAG: {ti.dag_id}",
                "color": 15158332,
                "fields": [
                    {"name": "Tâche", "value": ti.task_id, "inline": True},
                    {"name": "Logs", "value": f"[Voir les logs Airflow]({log_url})"},
                ],
                "footer": {"text": "SynkOS 2026"},
            }
        ],
    }

    webhook_url = os.getenv("URL_WEBHOOK_DIDI")
    if webhook_url:
        try:
            requests.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            print(f"Erreur Discord: {e}")
