import logging
import requests
import json
import os
from typing import Any

logger = logging.getLogger(__name__)


def extract_events_with_llm(raw_text: str) -> Any:
    raw_output = ""
    url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    model = os.getenv("LLM_MODEL", "mistral")

    prompt = f"""[INST] Extract the concerts from this OCR text into a JSON list.
    Use year 2026. April is month 04.
    Format: {{"date": "YYYY-MM-DD", "artist": "NAME", "type": "LIVE/DJ/CLUB"}}

    TEXT:
    {raw_text} [/INST]"""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
            "num_ctx": 4096,
        },
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        raw_output = result.get("response", "")

        data = json.loads(raw_output)
        if isinstance(data, dict):
            if "concerts" in data:
                return data["concerts"]
            if "events" in data:
                return data["events"]
            return [data]

        if isinstance(data, list):
            return data

        return []

    except Exception as e:
        logger.error(f"Erreur parsing LLM : {e}")
        logger.debug(f"Contenu reçu : {raw_output[:100]}...")
        return []
