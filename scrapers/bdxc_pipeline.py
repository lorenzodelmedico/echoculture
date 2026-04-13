import requests
import hashlib
import json
import logging
import os
from datetime import datetime
from pymongo import MongoClient
from psycopg2.extras import execute_values
from utils.db import pg_connection

MONGO_URI = os.getenv("MONGO_URL")

KNOWN_CITIES = [
    "Bordeaux",
    "Mérignac",
    "Pessac",
    "Talence",
    "Bègles",
    "Cenon",
    "Floirac",
    "Lormont",
]

GENRE_FAMILY_MAP = {
    "Rock": "Rock & Metal",
    "Metal": "Rock & Metal",
    "Punk": "Rock & Metal",
    "Hardcore": "Rock & Metal",
    "Garage": "Rock & Metal",
    "Techno": "Électronique",
    "Electro": "Électronique",
    "House": "Électronique",
    "DJ set": "Électronique",
    "Dub": "Électronique",
    "Jazz": "Jazz & Soul",
    "Blues": "Jazz & Soul",
    "Soul": "Jazz & Soul",
    "Funk": "Jazz & Soul",
    "Swing": "Jazz & Soul",
    "Hip-Hop": "Hip-Hop & RnB",
    "RnB": "Hip-Hop & RnB",
    "Classique": "Classique & Contemp.",
    "Musique Contemporaine": "Classique & Contemp.",
    "Folk": "Classique & Contemp.",
    "Chanson": "Chanson & Pop",
    "Pop": "Chanson & Pop",
    "Variete": "Chanson & Pop",
    "Musiques du monde": "Musiques du monde",
    "Musiques Latines": "Musiques du monde",
    "Reggae": "Musiques du monde",
    "Ciné-concert": "Spectacles",
    "Cirque": "Spectacles",
    "Slam": "Spectacles",
    "Spectacle musical": "Spectacles",
    "Comédie musicale": "Spectacles",
    "Opéra": "Spectacles",
    "Concert": "Concert",
}


def get_genre_family(genre: str) -> str:
    return GENRE_FAMILY_MAP.get(genre, genre)


def hash_payload(data):
    return hashlib.md5(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()


def extract_city(location_str):
    if not location_str:
        return "Autre"
    for city in KNOWN_CITIES:
        if city.lower() in location_str.lower():
            return city
    return "Autre"


def generate_signature(title, date_iso, location):
    raw = f"{title}{date_iso}{location}".lower().strip().replace(" ", "")
    return hashlib.md5(raw.encode()).hexdigest()


SCRAPE_MONTHS_AHEAD = 12


def process_bdxc():
    logging.info("Début du pipeline BDXC...")

    today = datetime.utcnow().date()
    # Calcul de la date de fin sur 12 mois (même jour, année +1)
    end_month = today.month
    end_year = today.year + (SCRAPE_MONTHS_AHEAD // 12)
    end_month += SCRAPE_MONTHS_AHEAD % 12
    if end_month > 12:
        end_month -= 12
        end_year += 1
    end_date = today.replace(year=end_year, month=end_month)

    API_URL = "https://www.bdxc.fr/frontend-api/representations"
    HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EchoCulture-scraper/1.0)"}
    params = {
        "category": "concerts",
        "department": "33",
        "start": today.isoformat(),
        "end": end_date.isoformat(),
        "page_size": 1000,
    }

    logging.info(f"Scraping BDXC du {today} au {end_date}...")
    try:
        response = requests.get(API_URL, headers=HEADERS, params=params, timeout=60)
        response.raise_for_status()
        payload = response.json()
    except Exception as e:
        logging.error(f"Erreur lors de l'appel API BDXC: {e}")
        raise

    if isinstance(payload, dict):
        events = (
            payload.get("events")
            or payload.get("data")
            or payload.get("representations")
            or []
        )
    else:
        logging.error(f"Format inattendu : {type(payload)}")
        raise RuntimeError(f"Format API BDXC inattendu : {type(payload)}")

    if not isinstance(events, list):
        logging.error(f"Impossible d'extraire une liste : {type(events)}")
        raise RuntimeError("Liste d'événements introuvable dans la réponse BDXC")

    logging.info(
        f"{len(events)} événements reçus ({today} → {end_date}). Traitement en cours..."
    )

    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client["echoculture_bronze"]
    col_raw = db["bdxc_events_raw"]
    col_sync = db["bdxc_sync_history"]

    current_hash = hash_payload(events)
    last_sync = col_sync.find_one(sort=[("timestamp", -1)])

    if last_sync and last_sync.get("payload_hash") == current_hash:
        logging.info(
            "Aucune modification BDXC détectée depuis le dernier run. Fin du pipeline."
        )
        return

    today_str = datetime.utcnow().isoformat()
    col_raw.insert_one({"timestamp": today_str, "events": events})
    logging.info(
        f"Nouveau payload BDXC détecté (Hash: {current_hash}). Traitement en cours..."
    )

    silver_events = []

    for ev in events:
        if not isinstance(ev, dict):
            logging.warning(
                f"Événement ignoré (pas un dict) : {type(ev)} — {str(ev)[:80]}"
            )
            continue

        venue = ev.get("venue") or ""
        city_raw = ev.get("location") or ""
        loc = venue
        city = extract_city(city_raw) if city_raw else "Bordeaux"
        title = ev.get("title", "Sans titre")
        start_date = ev.get("startDate")

        if not start_date:
            continue

        sig = generate_signature(title, start_date, loc)
        event_type = ev.get("primaryStyleName") or "Concert"
        genre_family = get_genre_family(event_type)
        url_billetterie = ev.get("ticketingUrl")
        raw_id = str(ev.get("id", ""))

        silver_events.append(
            (
                sig,
                "BDXC",
                title,
                event_type,
                genre_family,
                start_date,
                ev.get("date", ""),
                loc,
                city,
                url_billetterie,
                raw_id,
            )
        )

    if not silver_events:
        logging.warning("Aucun événement valide à insérer après filtrage.")
        return

    query = """
        INSERT INTO events
            (signature, source, title, event_type,
             genre_family, event_date, event_date_raw,
             location, city_computed,
             url_billetterie, raw_id)
        VALUES %s
        ON CONFLICT (signature) DO UPDATE SET
            city_computed = EXCLUDED.city_computed,
            url_billetterie = EXCLUDED.url_billetterie,
            title = EXCLUDED.title,
            event_type = EXCLUDED.event_type,
            genre_family = EXCLUDED.genre_family,
            location = EXCLUDED.location;
    """

    try:
        with pg_connection() as conn:
            cur = conn.cursor()
            execute_values(cur, query, silver_events)
            cur.close()
    except Exception as e:
        logging.error(f"Erreur fatale lors de l'insertion Postgres : {e}")
        raise

    # NOTE: hash enregistré seulement après succès Postgres — si Postgres crash,
    # le prochain run re-traite les données plutôt que de les ignorer silencieusement.
    col_sync.insert_one({"timestamp": today_str, "payload_hash": current_hash})
    logging.info(
        f"✅ Pipeline BDXC terminé. {len(silver_events)} "
        "événements insérés/mis à jour dans Postgres."
    )


if __name__ == "__main__":
    # pour tests manuels en CLI : python scrapers/bdxc_pipeline.py
    process_bdxc()
