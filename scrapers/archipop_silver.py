import os
import asyncio
import hashlib
import psycopg
from motor.motor_asyncio import AsyncIOMotorClient
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from utils.ocr_engine import extract_text_from_url
from utils.llm_engine import extract_events_with_llm

load_dotenv()
SOURCE_NAME = "archi-pop"

# --- MODULES DE TRAITEMENT ---


def extract_image_url(html_content):
    """Trouve l'URL de l'image de programmation"""
    soup = BeautifulSoup(html_content, "html.parser")
    # On cherche l'image avec le alt qui commence par 'Programmation'
    img = soup.find("img", alt=lambda x: x and x.startswith("Programmation"))
    return img["src"] if img else None


# --- CORE LOGIC ---


async def run_silver_transformation():
    # 1. Connexions
    db_url = os.getenv("POSTGRES_URL")
    mongo_url = os.getenv("MONGO_URL")

    mongo_client = AsyncIOMotorClient(mongo_url)
    db_mongo = mongo_client.echoculture
    pg_conn = await psycopg.AsyncConnection.connect(db_url)

    try:

        raw_doc = await db_mongo.raw_events.find_one(
            {"source": SOURCE_NAME}, sort=[("scraped_at", -1)]
        )

        if not raw_doc:
            print(f"❌ Aucune donnée Bronze trouvée pour '{SOURCE_NAME}'.")
            return

        img_url = extract_image_url(raw_doc["payload"])
        if not img_url:
            return

        # --- ÉTAPE SILVER : OCR ---
        raw_text = extract_text_from_url(img_url)
        if not raw_text:
            print("❌ OCR vide.")
            return

        print("--- TEXTE RÉCUPÉRÉ ---")
        print(raw_text[:200] + "...")

        # --- ÉTAPE GOLD : LLM ---
        print("🧠 Structuration par LLM (Ollama) en cours...")
        structured_events = extract_events_with_llm(raw_text)

        async with pg_conn.cursor() as cur:

            if not structured_events:
                print("❌ Erreur critique : Ollama n'a rien renvoyé.")
                # On force l'erreur pour Airflow
                raise ValueError(
                    "Le LLM Ollama n'a pas répondu ou le parsing a échoué."
                )
            else:
                for ev in structured_events:
                    print(structured_events)
                    artist = ev.get("artist", "Inconnu")
                    event_type = ev.get("type", "EVENT")
                    date = ev.get("date")

                    signature = hashlib.md5(
                        f"{SOURCE_NAME}{artist}{date}".encode()
                    ).hexdigest()

                    print(f"📌 Gold : {date} | {artist} ({event_type})")
                    await cur.execute(
                        """
                        INSERT INTO events (signature, source, title, event_type,
                        event_date, location, raw_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (signature)
                        DO UPDATE SET
                            event_type = EXCLUDED.event_type,
                            raw_id = EXCLUDED.raw_id;
                        """,
                        (
                            signature,
                            SOURCE_NAME,
                            artist,
                            event_type,
                            date,
                            "Archi-Pop",
                            str(raw_doc["_id"]),
                        ),
                    )
            await pg_conn.commit()
        print(f"🚀 Terminé : {len(structured_events)} événements insérés.")

    finally:
        mongo_client.close()
        await pg_conn.close()


def run_silver_transformation_sync():
    return asyncio.run(run_silver_transformation())


if __name__ == "__main__":
    run_silver_transformation_sync()
