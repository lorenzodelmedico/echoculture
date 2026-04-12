import hashlib
import logging
import os
import re
import time
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_values
from bs4 import BeautifulSoup
from pymongo import MongoClient
import requests

PG_URL = os.getenv("POSTGRES_URL")
MONGO_URI = os.getenv("MONGO_URL", "mongodb://admin:mongopassword@db_mongodb:27017/")
CALENDAR_URL = "https://ecran-total.fr/calendrier/"


def parse_numeric_date(text: str):
    """Parse a date string like '15/04/2026' → date object."""
    from datetime import date

    text = text.strip()
    match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if match:
        day, month, year = match.groups()
        try:
            return date(int(year), int(month), int(day))
        except ValueError:
            pass
    return None


def make_signature(title: str, release_date) -> str:
    raw = f"{title}{release_date}".lower().strip()
    return hashlib.md5(raw.encode()).hexdigest()


def hash_html(html: str) -> str:
    return hashlib.md5(html.encode("utf-8")).hexdigest()


def fetch_html_with_playwright() -> str:
    """Fetch ecran-total.fr/calendrier/ using Playwright to bypass Cloudflare."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="fr-FR",
        )
        page = context.new_page()
        # Hide automation signals
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page.goto(CALENDAR_URL, wait_until="domcontentloaded", timeout=60000)
        # Give JS a moment to render content after DOM is ready
        page.wait_for_timeout(3000)
        # Wait for actual content (not the Cloudflare challenge page)
        try:
            page.wait_for_selector("article, .film, .movie, .post, main", timeout=15000)
        except Exception:
            logging.warning("Selector timeout — dumping whatever HTML we have")
        html: str = page.content()
        browser.close()
        return html


def parse_movies(html: str) -> list:
    """Parse movie data from ecran-total.fr HTML.

    Real structure (confirmed from live HTML dump):
      - Date headers: <h2 class="date-separator ...">DD/MM/YYYY</h2>
      - Film cards:   <div class="film-card production ...">
          <a class="full" href="URL" title="TITLE">
          <div class="titre extra-wide"><h3>TITLE</h3></div>
          <p class="societe distributeur"><a>DISTRIBUTOR</a></p>
          <p class="small status">STATUS</p>
    """
    soup = BeautifulSoup(html, "html.parser")
    movies = []
    current_release_date = None

    for el in soup.find_all(["h2", "div"]):
        classes = el.get("class", [])

        # --- Date header ---
        if el.name == "h2" and "date-separator" in classes:
            parsed = parse_numeric_date(el.get_text(strip=True))
            if parsed:
                current_release_date = parsed
                logging.info(f"📅 Date détectée : {current_release_date}")
            continue

        # --- Film card ---
        if "film-card" not in classes:
            continue

        # Title: <h3> inside .titre
        titre_div = el.find("div", class_="titre")
        title_el = titre_div.find("h3") if titre_div else None
        title = title_el.get_text(strip=True) if title_el else None
        if not title or len(title) < 2:
            continue

        # URL: <a class="full">
        link_el = el.find("a", class_="full")
        url = link_el["href"] if link_el else None

        # Distributor (stored in director field — closest available metadata)
        dist_p = el.find("p", class_="distributeur")
        distributor = None
        if dist_p:
            dist_a = dist_p.find("a")
            distributor = (
                dist_a.get_text(strip=True) if dist_a else dist_p.get_text(strip=True)
            )

        if not current_release_date:
            logging.debug(f"Film sans date ignoré : {title}")
            continue

        movies.append(
            {
                "title": title,
                "director": distributor,  # distributor mapped to director column
                "producer": None,
                "genres": None,
                "synopsis": None,
                "duration": None,
                "release_date": current_release_date,
                "url": url,
            }
        )
        logging.info(f"🎬 {title} ({current_release_date})")

    return movies


def fetch_wikipedia_genres(title: str) -> str | None:
    """Search Wikipedia for movie and extract genres from infobox.

    Args:
        title: Movie title to search on Wikipedia

    Returns:
        Comma-separated string of genres, or None if not found
    """
    if not title or len(title) < 2:
        return None

    try:
        # Search Wikipedia API for the movie
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": title,
            "format": "json",
            "srlimit": "5",
        }
        headers = {"User-Agent": "EchoCulture-Bot/1.0"}

        response = requests.get(
            search_url, params=search_params, headers=headers, timeout=10
        )
        response.raise_for_status()
        search_results = response.json()

        if not search_results.get("query", {}).get("search"):
            logging.debug(f"No Wikipedia results for: {title}")
            return None

        # Get the first (most relevant) result
        first_result = search_results["query"]["search"][0]
        page_title = first_result["title"]

        # Fetch the page content to extract genre from infobox
        content_params = {
            "action": "query",
            "titles": page_title,
            "prop": "extracts",
            "format": "json",
        }

        content_response = requests.get(
            search_url, params=content_params, headers=headers, timeout=10
        )
        content_response.raise_for_status()
        content_data = content_response.json()

        pages = content_data.get("query", {}).get("pages", {})
        if not pages:
            return None

        page = next(iter(pages.values()))
        extract_html = page.get("extract", "")

        # Parse HTML to find genre in infobox
        soup = BeautifulSoup(extract_html, "html.parser")

        # Look for infobox and genre field
        # Wikipedia infoboxes have structure like:
        # <th>Genre</th> followed by <td> with genre data
        genre_text = None
        for th in soup.find_all("th"):
            if "genre" in th.get_text(strip=True).lower():
                # Genre is usually in the next <td>
                tr = th.find_parent("tr")
                if tr:
                    next_td = tr.find_next("td")
                    if next_td:
                        genre_text = next_td.get_text(strip=True)
                        break
                else:
                    # Try finding next td in document
                    td = th.find_next("td")
                    if td:
                        genre_text = td.get_text(strip=True)
                        break

        if genre_text:
            # Clean up: remove citations [1], [2], etc., and extra whitespace
            genre_text = re.sub(r"\[\d+\]", "", genre_text)
            genre_text = re.sub(r"\s+", ", ", genre_text).strip()
            # Remove trailing commas
            genre_text = re.sub(r",\s*$", "", genre_text)
            if genre_text:
                logging.info(f"✓ Found on Wikipedia for '{title}': {genre_text}")
                return genre_text

        logging.debug(f"No genre found on Wikipedia for: {title}")
        return None

    except requests.exceptions.RequestException as e:
        logging.warning(f"Failed to fetch Wikipedia data for '{title}': {e}")
        return None
    except Exception as e:
        logging.warning(f"Error parsing Wikipedia genres for '{title}': {e}")
        return None


def process_ecrantotal():
    logging.info("Début du pipeline Écran Total (films)...")

    try:
        html = fetch_html_with_playwright()
    except Exception as e:
        logging.error(f"Erreur Playwright : {e}")
        raise

    if "Safeguarding" in html or "BigScoots" in html:
        raise RuntimeError(
            "Cloudflare challenge non contournée — "
            "Playwright a renvoyé la page de protection."
        )

    # Dump HTML to mounted volume for structure inspection
    debug_path = "/opt/airflow/logs/ecrantotal_debug.html"
    try:
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(html)
        logging.info(f"HTML dumped → {debug_path}")
    except Exception as e:
        logging.warning(f"Could not write debug HTML: {e}")

    # MongoDB hash guard — skip if page unchanged since last run
    mongo_client = MongoClient(MONGO_URI)
    col_sync = mongo_client["echoculture_bronze"]["ecrantotal_sync_history"]
    current_hash = hash_html(html)
    last_sync = col_sync.find_one(sort=[("timestamp", -1)])
    if last_sync and last_sync.get("payload_hash") == current_hash:
        logging.info(
            "Aucune modification Écran Total détectée "
            "depuis le dernier run. Fin du pipeline."
        )
        return

    movies = parse_movies(html)
    if not movies:
        raise RuntimeError(
            "Aucun film parsé — voir "
            "/opt/airflow/logs/ecrantotal_debug.html "
            "pour inspecter la structure HTML."
        )

    logging.info(
        f"{len(movies)} films parsés. Extraction des genres depuis Wikipedia..."
    )

    # Fetch genres from Wikipedia (with rate limiting)
    for i, movie in enumerate(movies):
        genres = fetch_wikipedia_genres(movie["title"])
        if genres:
            movie["genres"] = genres
        # Rate limit: 0.5 seconds between requests to avoid overwhelming Wikipedia
        if i < len(movies) - 1:  # Don't sleep after the last movie
            time.sleep(0.5)

    logging.info("Genres extraction complète. Insertion dans Postgres...")

    rows = []
    for m in movies:
        sig = make_signature(m["title"], m["release_date"])
        rows.append(
            (
                sig,
                m["title"],
                m.get("director"),
                m.get("producer"),
                m.get("genres"),
                m.get("synopsis"),
                m["release_date"],
                m.get("duration"),
                m.get("url"),
            )
        )

    try:
        conn = psycopg2.connect(PG_URL)
        cur = conn.cursor()
        query = """
            INSERT INTO movies
                (signature, title, director, producer,
                 genres, synopsis, release_date,
                 duration, url)
            VALUES %s
            ON CONFLICT (signature) DO UPDATE SET
                director   = EXCLUDED.director,
                producer   = EXCLUDED.producer,
                genres     = EXCLUDED.genres,
                synopsis   = EXCLUDED.synopsis,
                duration   = EXCLUDED.duration,
                url        = EXCLUDED.url;
        """
        execute_values(cur, query, rows)
        conn.commit()
        cur.close()
        conn.close()
        logging.info(f"✅ {len(rows)} films insérés/mis à jour dans Postgres.")
        # Record hash only after successful Postgres write
        col_sync.insert_one(
            {"timestamp": datetime.utcnow().isoformat(), "payload_hash": current_hash}
        )
        logging.info(f"Hash Écran Total enregistré : {current_hash}")
    except Exception as e:
        logging.error(f"Erreur Postgres : {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    process_ecrantotal()
