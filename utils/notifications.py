import requests
import os


def send_discord_alert(context):
    # Récupération des infos de l'échec
    ti = context.get("task_instance")
    dag_id = ti.dag_id
    task_id = ti.task_id
    log_url = ti.log_url
    execution_date = context.get("execution_date").strftime("%Y-%m-%d %H:%M")

    # Message formaté pour Discord (Markdown)
    payload = {
        "content": "🚨 **ALERTE : ÉCHEC DE TÂCHE AIRFLOW** 🚨",
        "embeds": [
            {
                "title": f"DAG: {dag_id}",
                "color": 15158332,  # Rouge
                "fields": [
                    {"name": "Tâche", "value": task_id, "inline": True},
                    {"name": "Date", "value": execution_date, "inline": True},
                    {
                        "name": "Logs",
                        "value": f"[Cliquer ici pour voir les logs]({log_url})",
                    },
                ],
                "footer": {"text": "EchoCulture Pipeline Monitoring"},
            }
        ],
    }

    # Ton URL Discord Webhook
    webhook_url = os.getenv("URL_WEBHOOK_DIDI")

    try:
        requests.post(webhook_url, json=payload, timeout=10)
    except Exception as e:
        print(f"Impossible d'envoyer l'alerte Discord : {e}")
