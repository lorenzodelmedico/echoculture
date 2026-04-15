import hashlib
import logging
import os
import re
import time
from datetime import datetime

from psycopg2.extras import execute_values
from bs4 import BeautifulSoup
from pymongo import MongoClient
import requests

from utils.db import pg_connection

MONGO_URI = os.getenv("MONGO_URL")
CALENDAR_URL = "https://ecran-total.fr/calendrier/"
HEADERS = {"User-Agent": "EchoCulture/1.0"}


def parse_numeric_date(text: str):
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
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page.goto(CALENDAR_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        try:
            page.wait_for_selector("article, .film, .movie, .post, main", timeout=15000)
        except Exception:
            logging.warning("Selector timeout — dumping whatever HTML we have")
        html: str = page.content()
        browser.close()
        return html


def parse_movies(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    movies = []
    current_release_date = None

    for el in soup.find_all(["h2", "div"]):
        classes = el.get("class", [])

        if el.name == "h2" and "date-separator" in classes:
            parsed = parse_numeric_date(el.get_text(strip=True))
            if parsed:
                current_release_date = parsed
                logging.info(f"📅 Date détectée : {current_release_date}")
            continue

        if "film-card" not in classes:
            continue

        titre_div = el.find("div", class_="titre")
        title_el = titre_div.find("h3") if titre_div else None
        title = title_el.get_text(strip=True) if title_el else None
        if not title or len(title) < 2:
            continue

        link_el = el.find("a", class_="full")
        url = link_el["href"] if link_el else None

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
                "director": distributor,
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


_GENRE_KEYWORDS: dict[str, str] = {
    "action": "Action",
    "adventure": "Adventure",
    "animated": "Animation",
    "animation": "Animation",
    "biographical": "Biography",
    "biography": "Biography",
    "comedy": "Comedy",
    "crime": "Crime",
    "documentary": "Documentary",
    "drama": "Drama",
    "fantasy": "Fantasy",
    "historical": "History",
    "horror": "Horror",
    "musical": "Musical",
    "mystery": "Mystery",
    "romance": "Romance",
    "romantic": "Romance",
    "science fiction": "Science fiction",
    "sci-fi": "Science fiction",
    "sport": "Sport",
    "sports": "Sport",
    "superhero": "Superhero",
    "thriller": "Thriller",
    "war": "War",
    "western": "Western",
}

_WIKI_FETCH_PARAMS: dict = {
    "action": "query",
    "prop": "categories|extracts",
    "clshow": "!hidden",
    "cllimit": "50",
    "exintro": True,
    "explaintext": True,
    "exsectionformat": "plain",
    "format": "json",
}


def _wiki_request(url: str, params: dict):
    resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
    if resp.status_code == 429:
        return {}
    resp.raise_for_status()
    return resp.json()


def _extract_genres(categories: list[str], intro: str) -> str | None:
    found: list[str] = []
    seen: set[str] = set()
    for cat in categories:
        cat_lower = cat.lower()
        if "film" not in cat_lower:
            continue
        for keyword, label in sorted(_GENRE_KEYWORDS.items(), key=lambda x: -len(x[0])):
            if keyword in cat_lower and label not in seen:
                found.append(label)
                seen.add(label)
    if found:
        return ", ".join(found)
    match = re.search(r"\bis an?\s+(.{3,80})\s+film\b", intro, re.IGNORECASE)
    if match:
        phrase = match.group(1).lower()
        for keyword, label in sorted(_GENRE_KEYWORDS.items(), key=lambda x: -len(x[0])):
            if keyword in phrase and label not in seen:
                found.append(label)
                seen.add(label)
    return ", ".join(found) if found else None


def _fetch_en_genres(en_title: str) -> str | None:
    try:
        data = _wiki_request(
            "https://en.wikipedia.org/w/api.php",
            {"titles": en_title, **_WIKI_FETCH_PARAMS},
        )
        for page in data.get("query", {}).get("pages", {}).values():
            cats = [
                c["title"].replace("Category:", "") for c in page.get("categories", [])
            ]
            intro = page.get("extract", "")
            return _extract_genres(cats, intro)
    except requests.RequestException:
        pass
    return None


def fetch_wikipedia_genres(title: str) -> str | None:
    if not title or len(title) < 2:
        return None

    try:
        data = _wiki_request(
            "https://en.wikipedia.org/w/api.php",
            {
                "action": "query",
                "list": "search",
                "srsearch": f"{title} film",
                "format": "json",
                "srlimit": 1,
            },
        )
        results = data.get("query", {}).get("search", [])
        if results:
            genres = _fetch_en_genres(results[0]["title"])
            if genres:
                return genres
    except requests.RequestException:
        pass

    try:
        data = _wiki_request(
            "https://fr.wikipedia.org/w/api.php",
            {
                "action": "query",
                "list": "search",
                "srsearch": title,
                "format": "json",
                "srlimit": 1,
            },
        )
        results = data.get("query", {}).get("search", [])
        if not results:
            return None
        fr_title = results[0]["title"]
    except requests.RequestException as e:
        logging.warning(f"Wikipedia search failed for {title!r}: {e}")
        return None

    try:
        data = _wiki_request(
            "https://fr.wikipedia.org/w/api.php",
            {
                "action": "query",
                "prop": "langlinks|categories|extracts",
                "lllang": "en",
                "clshow": "!hidden",
                "cllimit": "50",
                "exintro": True,
                "explaintext": True,
                "exsectionformat": "plain",
                "titles": fr_title,
                "format": "json",
            },
        )
        pages = data.get("query", {}).get("pages", {})
    except requests.RequestException as e:
        logging.warning(f"Wikipedia fetch failed for {fr_title!r}: {e}")
        return None

    for page in pages.values():
        en_links = [
            lk["*"] for lk in page.get("langlinks", []) if lk.get("lang") == "en"
        ]
        fr_cats = [
            c["title"].replace("Catégorie:", "").replace("Category:", "")
            for c in page.get("categories", [])
        ]
        fr_intro = page.get("extract", "")

        if en_links:
            genres = _fetch_en_genres(en_links[0])
            if genres:
                return genres

        return _extract_genres(fr_cats, fr_intro)

    return None


def process_ecrantotal(skip_enrichment: bool = False):
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
        log_dir = os.getenv("AIRFLOW_LOG_DIR", "/opt/airflow/logs")
        debug_path = os.path.join(log_dir, "ecrantotal_debug.html")
        try:
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(html)
            logging.warning(f"Aucun film parsé — HTML dumped → {debug_path}")
        except Exception:
            pass
        raise RuntimeError("Aucun film parsé — voir les logs pour inspecter le HTML.")

    logging.info(
        f"{len(movies)} films parsés. Extraction des genres depuis Wikipedia..."
    )

    # Load genres from DB to skip re-hitting Wikipedia.
    # Skip dirty values from the old wikitext approach (markup or French phrases).
    existing_genres: dict[str, str] = {}
    try:
        with pg_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT title, genres FROM movies WHERE genres IS NOT NULL")
            existing_genres = {
                row[0]: row[1]
                for row in cur.fetchall()
                if "[[" not in row[1] and "film de" not in row[1].lower()
            }
            cur.close()
    except Exception:
        pass

    needs_lookup = [m for m in movies if m["title"] not in existing_genres]
    for m in movies:
        if m["title"] in existing_genres:
            m["genres"] = existing_genres[m["title"]]

    logging.info(
        f"{len(existing_genres)} genres récupérés depuis la DB, "
        f"{len(needs_lookup)} films à chercher sur Wikipedia."
    )

    if skip_enrichment:
        logging.info(
            "Genre enrichment skipped (skip_enrichment=True) — "
            "Spark job will handle it after insertion."
        )
    else:
        for i, movie in enumerate(needs_lookup):
            genres = fetch_wikipedia_genres(movie["title"])
            if genres:
                movie["genres"] = genres
            if i < len(needs_lookup) - 1:
                time.sleep(1.5)

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

    query = """
        INSERT INTO movies
            (signature, title, director, producer,
             genres, synopsis, release_date,
             duration, url)
        VALUES %s
        ON CONFLICT (signature) DO UPDATE SET
            director   = EXCLUDED.director,
            producer   = EXCLUDED.producer,
            genres     = COALESCE(EXCLUDED.genres, movies.genres),
            synopsis   = EXCLUDED.synopsis,
            duration   = EXCLUDED.duration,
            url        = EXCLUDED.url;
    """

    try:
        with pg_connection() as conn:
            cur = conn.cursor()
            execute_values(cur, query, rows)
            cur.close()
    except Exception as e:
        logging.error(f"Erreur Postgres : {e}")
        raise

    logging.info(f"✅ {len(rows)} films insérés/mis à jour dans Postgres.")
    # NOTE: hash enregistré seulement après succès Postgres
    col_sync.insert_one(
        {"timestamp": datetime.utcnow().isoformat(), "payload_hash": current_hash}
    )
    logging.info(f"Hash Écran Total enregistré : {current_hash}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    process_ecrantotal()
