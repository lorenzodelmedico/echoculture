import logging
import random
import re
import time
import urllib.parse
from datetime import date

import requests
from bs4 import BeautifulSoup

from utils.db import pg_connection

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EchoCulture-scraper/1.0)"}

_NOISE_LABELS = {"Payant", "Tarification", "Tarif"}


def generate_bdxc_url(slug: str, location: str, start_date: str) -> str | None:
    if not slug or not start_date:
        return None
    date_part = start_date[:10]
    loc = urllib.parse.quote(location.lower().replace(" ", "-"))
    return f"https://www.junklive.fr/evenements/{loc}/{date_part}/{slug}/"


def fetch_event_page(url: str) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        logging.warning(f"Price fetch failed for {url}: {e}")
        return None


def extract_prices_from_html(html: str) -> tuple[list[dict], str | None]:
    """Return (prices, price_tag).

    price_tag is 'payant' when the page confirms the event is paid but gives
    no specific amount. None in all other cases.
    """
    soup = BeautifulSoup(html, "html.parser")
    lines = [
        ln.strip() for ln in soup.get_text(separator="\n").split("\n") if ln.strip()
    ]

    for i, line in enumerate(lines):
        if "Tarification" not in line:
            continue

        # Universally free — known free labels as the first content after the header
        next_line = lines[i + 1] if i + 1 < len(lines) else ""
        if next_line.startswith("Gratuit"):
            return [{"label": "Gratuit", "amount": 0.0}], None
        if next_line.startswith("Prix libre"):
            return [{"label": "Prix libre", "amount": 0.0}], None
        if next_line.startswith("Entrée libre"):
            return [{"label": "Entrée libre", "amount": 0.0}], None

        prices = []
        payant_found = False
        window = lines[i + 1 : i + 20]

        for j, sub in enumerate(window):
            prev = window[j - 1] if j > 0 else ""
            label_from_prev = (
                prev
                if prev and prev not in _NOISE_LABELS and "€" not in prev
                else "Entrée"
            )
            # Range format: "de X,XX à Y€" — captures both min and max
            range_m = re.search(
                r"de\s+(\d+[.,]?\d*)\s*€?\s*à\s+(\d+[.,]?\d*)\s*€",
                sub,
                re.IGNORECASE,
            )
            if range_m:
                min_a = float(range_m.group(1).replace(",", "."))
                max_a = float(range_m.group(2).replace(",", "."))
                prices.append({"label": f"{label_from_prev} (dès)", "amount": min_a})
                prices.append({"label": label_from_prev, "amount": max_a})
                continue
            # Single paid price line
            m = re.search(r"(\d+[.,]?\d*)\s*€", sub)
            if m:
                amount = float(m.group(1).replace(",", "."))
                prices.append({"label": label_from_prev, "amount": amount})
            # Conditional free entry — "Gratuit" with a meaningful preceding label
            elif sub == "Gratuit" and j > 0:
                prev = window[j - 1]
                if prev and prev not in _NOISE_LABELS and "€" not in prev:
                    prices.append({"label": f"Gratuit ({prev})", "amount": 0.0})
            # "Entrée libre" anywhere in the window
            elif sub.startswith("Entrée libre"):
                prices.append({"label": "Entrée libre", "amount": 0.0})
            # "Prix libre" anywhere in the window
            elif sub.startswith("Prix libre"):
                prices.append({"label": "Prix libre", "amount": 0.0})
            # "Payant" with no specific amount — remember it
            elif sub == "Payant":
                payant_found = True

        if prices:
            return prices, None
        if payant_found:
            return [], "payant"
        return [], None

    return [], None


def process_bdxc_prices():
    logging.info("Début du pipeline prix BDXC...")

    today = date.today()

    try:
        with pg_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT signature, source_url
                FROM events
                WHERE source_url IS NOT NULL
                  AND event_date >= %s
                  AND min_price IS NULL
                  AND price_tag IS NULL
                ORDER BY event_date
                """,
                (today,),
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

        prices, price_tag = extract_prices_from_html(html)
        if not prices and not price_tag:
            if i < len(targets) - 1:
                time.sleep(random.uniform(1.0, 2.0))
            continue

        try:
            with pg_connection() as conn:
                cur = conn.cursor()
                if prices:
                    amounts = [p["amount"] for p in prices]
                    free_label = next(
                        (p["label"] for p in prices if p["amount"] == 0.0), None
                    )
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
                        SET min_price = %s, max_price = %s,
                            free_label = %s, price_tag = NULL
                        WHERE signature = %s
                        """,
                        (min(amounts), max(amounts), free_label, signature),
                    )
                else:
                    # price_tag = 'payant': confirmed paid but no specific amount
                    cur.execute(
                        """
                        UPDATE events
                        SET price_tag = %s
                        WHERE signature = %s
                        """,
                        (price_tag, signature),
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
