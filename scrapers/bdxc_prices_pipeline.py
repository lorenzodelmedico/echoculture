import logging
import os
import random
import re
import time
import urllib.parse
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

from utils.db import pg_connection

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EchoCulture-scraper/1.0)"}
MAX_PRICE_SCRAPE = int(os.getenv("MAX_PRICE_SCRAPE", "100"))
PRICE_SCRAPE_DAYS_AHEAD = int(os.getenv("PRICE_SCRAPE_DAYS_AHEAD", "60"))


def generate_bdxc_url(slug: str, location: str, start_date: str) -> str | None:
    if not slug or not start_date:
        return None
    date_part = start_date[:10]
    loc = urllib.parse.quote(location.lower().replace(" ", "-"))
    return f"https://www.bdxc.fr/evenements/{loc}/{date_part}/{slug}/"


def fetch_event_page(url: str) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        logging.warning(f"Price fetch failed for {url}: {e}")
        return None


def extract_prices_from_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    lines = [
        ln.strip() for ln in soup.get_text(separator="\n").split("\n") if ln.strip()
    ]

    for i, line in enumerate(lines):
        if "Tarification" not in line:
            continue
        if i + 1 < len(lines) and "Gratuit" in lines[i + 1]:
            return [{"label": "Gratuit", "amount": 0.0}]
        prices = []
        window = lines[i + 1 : i + 11]
        for j, sub in enumerate(window):
            m = re.search(r"(\d+[.,]?\d*)\s*€", sub)
            if m:
                amount = float(m.group(1).replace(",", "."))
                label = window[j - 1] if j > 0 else "Tarif Unique"
                if label in ("Payant",) or "€" in label:
                    label = "Entrée"
                prices.append({"label": label, "amount": amount})
        return prices

    return []


def process_bdxc_prices():
    logging.info("Début du pipeline prix BDXC...")

    today = date.today()
    cutoff = today + timedelta(days=PRICE_SCRAPE_DAYS_AHEAD)

    try:
        with pg_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT signature, source_url
                FROM events
                WHERE source_url IS NOT NULL
                  AND event_date >= %s
                  AND event_date <= %s
                  AND min_price IS NULL
                ORDER BY event_date
                LIMIT %s
                """,
                (today, cutoff, MAX_PRICE_SCRAPE),
            )
            targets = cur.fetchall()
            cur.close()
    except Exception as e:
        logging.error(f"Erreur lecture Postgres : {e}")
        raise

    logging.info(f"{len(targets)} événements à pricer.")

    found = 0
    for i, (signature, source_url) in enumerate(targets):
        html = fetch_event_page(source_url)
        if html is None:
            continue

        prices = extract_prices_from_html(html)
        if not prices:
            if i < len(targets) - 1:
                time.sleep(random.uniform(1.0, 2.0))
            continue

        amounts = [p["amount"] for p in prices]
        try:
            with pg_connection() as conn:
                cur = conn.cursor()
                for p in prices:
                    cur.execute(
                        """
                        INSERT INTO event_prices (event_signature, label, amount)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (event_signature, label) DO UPDATE
                            SET amount = EXCLUDED.amount,
                                scraped_at = CURRENT_TIMESTAMP
                        """,
                        (signature, p["label"], p["amount"]),
                    )
                cur.execute(
                    """
                    UPDATE events
                    SET min_price = %s, max_price = %s
                    WHERE signature = %s
                    """,
                    (min(amounts), max(amounts), signature),
                )
                cur.close()
            found += 1
        except Exception as e:
            logging.error(f"Erreur insertion prix pour {signature}: {e}")

        if i < len(targets) - 1:
            time.sleep(random.uniform(1.0, 2.0))

    logging.info(
        f"✅ Prix BDXC terminé. {found}/{len(targets)} événements avec prix trouvés."
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    process_bdxc_prices()
