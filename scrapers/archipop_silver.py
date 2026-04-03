import os
import asyncio
import psycopg
from motor.motor_asyncio import AsyncIOMotorClient
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from utils.ocr_engine import extract_text_from_url

load_dotenv()

# --- MODULES DE TRAITEMENT ---


async def create_tables(pg_conn):
    """Crée la table events si elle n'existe pas (Auto-migration)"""
    async with pg_conn.cursor() as cur:
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id SERIAL PRIMARY KEY,
                source VARCHAR(50) NOT NULL,
                title TEXT NOT NULL,
                event_date_raw TEXT, -- Texte brut extrait de l'image
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
    mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
    db_mongo = mongo_client.echoculture

    pg_conn = await psycopg.AsyncConnection.connect(
        "host=localhost dbname=echoculture user=lorenzo password=echopassword"
    )

    try:
        # A. Préparer la DB SQL
        await create_tables(pg_conn)
        print("📁 Table Postgres prête.")

        # B. Récupérer le dernier document Bronze SPÉCIFIQUE à Archi-Pop
        raw_doc = await db_mongo.raw_events.find_one(
            {"source": "archi-pop"},  # Filtre : je ne veux que du Archi-Pop
            sort=[("scraped_at", -1)],  # Tri : je veux le plus récent
        )
        if not raw_doc:
            print("❌ Aucune donnée Bronze trouvée.")
            return

        # C. Extraire l'image
        img_url = extract_image_url(raw_doc["payload"])
        if img_url:
            print(f"🖼️ Image de programmation trouvée : {img_url}")
            # TODO : Ici on ajoutera la brique OCR pour lire le contenu de l'image
        else:
            print("⚠️ Pas d'image de programmation trouvée.")

        # D. Extraction Modulaire
        if img_url:
            raw_text = extract_text_from_url(img_url)

            if raw_text:
                print("--- TEXTE RÉCUPÉRÉ ---")
                print(raw_text[:500] + "...")  # On affiche un extrait

                # E. Insertion (Update ou Insert selon ta logique)
                async with pg_conn.cursor() as cur:
                    await cur.execute(
                        "INSERT INTO events (source, title, event_date_raw, raw_id) "
                        "VALUES (%s, %s, %s, %s)",
                        (
                            "archipop",
                            "Programmation Image",
                            raw_text,
                            str(raw_doc["_id"]),
                        ),
                    )
                    await pg_conn.commit()
                print("🚀 Texte OCR stocké en base.")
            else:
                print("❌ L'OCR n'a rien renvoyé.")
    finally:
        mongo_client.close()
        await pg_conn.close()


if __name__ == "__main__":
    asyncio.run(run_silver_transformation())
