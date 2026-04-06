import requests
import json
import os
from typing import Any


def extract_events_with_llm(raw_text: str) -> Any:
    url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

    prompt = f"""[INST] Extract the concerts from this OCR text into a JSON list.
    Use year 2026. April is month 04.
    Format: {{"date": "YYYY-MM-DD", "artist": "NAME", "type": "LIVE/DJ/CLUB"}}

    TEXT:
    {raw_text} [/INST]"""

    payload = {
        "model": "mistral",
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
            "num_ctx": 4096,  # On s'assure qu'il a assez de mémoire pour tout le texte
        },
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        result = response.json()
        raw_output = result.get("response", "")

        data = json.loads(raw_output)
        # print(raw_output)
        if isinstance(data, dict):
            if "concerts" in data:
                return data["concerts"]
            if "events" in data:
                return data["events"]
            return [data]  # Un seul objet

        if isinstance(data, list):
            return data

        return []

    except Exception as e:
        print(f"❌ Erreur parsing : {e}")
        print(f"CONTENU REÇU : {raw_output[:100]}...")
        return []
