import asyncio
import os
import requests
from bs4 import BeautifulSoup
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from dotenv import load_dotenv

# 1. Chargement des secrets (.env)
load_dotenv()


def run_bronze_scraping():
    asyncio.run(run_bronze_extraction())


async def run_bronze_extraction():
    """
    COUCHE BRONZE - Extraction brute de la page d'accueil d'Archi-Pop
    """
    # Connexion à MongoDB via l'URL du .env
    mongo_uri = os.getenv("MONGO_URL")
    client = AsyncIOMotorClient(mongo_uri)
    db = client.echoculture
    collection = db.raw_events

    print("🛰️  Connexion à Archi-Pop (https://archi-pop.com/)...")

    try:
        # On utilise requests pour le GET (Simple et efficace pour du statique)
        response = requests.get("https://archi-pop.com/", timeout=10)
        response.raise_for_status()

        # On parse juste pour vérifier que c'est du HTML, mais on garde TOUT
        soup = BeautifulSoup(response.text, "html.parser")

        # On prépare le document
        document = {
            "source": "archi-pop",
            "scraped_at": datetime.now(timezone.utc),
            "payload": str(soup),  # On stocke tout le HTML en string
            "format": "html",
            "status": "raw",
        }

        # Insertion dans la collection Bronze
        result = await collection.insert_one(document)
        print(f"✅ Succès ! Donnée Bronze insérée. ID : {result.inserted_id}")

    except Exception as e:
        print(f"💥 Erreur lors de l'extraction : {e}")
    finally:
        client.close()


if __name__ == "__main__":
    run_bronze_scraping()
