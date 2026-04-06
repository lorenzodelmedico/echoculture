import os
import asyncio
import psycopg
from motor.motor_asyncio import AsyncIOMotorClient
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from utils.ocr_engine import extract_text_from_url
from utils.llm_engine import extract_events_with_llm

load_dotenv()
SOURCE_NAME = "archi-pop"

# --- MODULES DE TRAITEMENT ---


async def create_tables(pg_conn):
    """Crée la table events si elle n'existe pas (Auto-migration)"""
    async with pg_conn.cursor() as cur:
        await cur.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        id SERIAL PRIMARY KEY,
                        source VARCHAR(50) NOT NULL,
                        title TEXT NOT NULL,
                        event_type VARCHAR(50),
                        event_date DATE,
                        location TEXT,
                        raw_id VARCHAR(50),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
        await pg_conn.commit()


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
        await create_tables(pg_conn)

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
            # 1. On nettoie les anciens événements pour cette source/image
            # (Évite les doublons si tu relances le script)
            await cur.execute(
                "DELETE FROM events WHERE raw_id = %s", (str(raw_doc["_id"]),)
            )

            if not structured_events:
                # Fallback : on log au moins l'OCR
                await cur.execute(
                    """INSERT INTO events (source, title, event_date_raw, raw_id)
                       VALUES (%s, %s, %s, %s)""",
                    (SOURCE_NAME, "LOG_OCR_ONLY", raw_text, str(raw_doc["_id"])),
                )
            else:
                for ev in structured_events:
                    print(structured_events)
                    artist = ev.get("artist", "Inconnu")
                    event_type = ev.get("type", "EVENT")
                    date = ev.get("date")

                    print(f"📌 Gold : {date} | {artist} ({event_type})")
                    await cur.execute(
                        """
                        INSERT INTO events (source, title, event_type,
                        event_date, location, raw_id)
                        VALUES (%s, %s, %s, %s, %s, %s)""",
                        (
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


if __name__ == "__main__":
    asyncio.run(run_silver_transformation())
