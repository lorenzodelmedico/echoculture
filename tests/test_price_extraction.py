import pytest
from scrapers.bdxc_prices_pipeline import (
    extract_prices_from_html,
    fetch_event_page,
    generate_bdxc_url,
)

# --- generate_bdxc_url ---


def test_generate_url_basic():
    url = generate_bdxc_url("rock-school-test", "Bordeaux", "2026-04-15T18:30:00Z")
    assert url == "https://www.bdxc.fr/evenements/bordeaux/2026-04-15/rock-school-test/"


def test_generate_url_accented_city():
    url = generate_bdxc_url("some-event", "Mérignac", "2026-05-01T20:00:00Z")
    assert url is not None
    assert "m%C3%A9rignac" in url or "merignac" in url.lower()


def test_generate_url_missing_slug():
    assert generate_bdxc_url("", "Bordeaux", "2026-04-15T18:30:00Z") is None


def test_generate_url_missing_date():
    assert generate_bdxc_url("some-slug", "Bordeaux", "") is None


# --- extract_prices_from_html ---


def _wrap(body: str) -> str:
    return f"<html><body>{body}</body></html>"


def test_extract_prices_free():
    html = _wrap("<p>Tarification</p><p>Gratuit</p>")
    result = extract_prices_from_html(html)
    assert result == [{"label": "Gratuit", "amount": 0.0}]


def test_extract_prices_paid_single():
    html = _wrap("<p>Tarification</p><p>Payant</p><p>8 €</p>")
    result = extract_prices_from_html(html)
    assert len(result) == 1
    assert result[0]["amount"] == 8.0
    assert result[0]["label"] == "Entrée"


def test_extract_prices_multiple():
    html = _wrap(
        "<p>Tarification</p><p>Payant</p>"
        "<p>Tarif Réduit</p><p>6 €</p>"
        "<p>Plein Tarif</p><p>12 €</p>"
    )
    result = extract_prices_from_html(html)
    assert len(result) == 2
    amounts = {r["amount"] for r in result}
    assert 6.0 in amounts
    assert 12.0 in amounts


def test_extract_prices_no_section():
    html = _wrap("<p>Aucune info de tarif ici.</p>")
    result = extract_prices_from_html(html)
    assert result == []


def test_extract_prices_decimal():
    html = _wrap("<p>Tarification</p><p>Entrée</p><p>12,50 €</p>")
    result = extract_prices_from_html(html)
    assert len(result) == 1
    assert result[0]["amount"] == 12.5


# --- integration (hits real network) ---


@pytest.mark.integration
def test_fetch_real_bdxc_price_page():
    url = """https://www.bdxc.fr/evenements/bordeaux/2026-04-15/
    rock-school-barbey-mercredi-15-avril-2026/"""
    html = fetch_event_page(url)
    assert html is not None, "Page returned None — may be 404 or network error"
    assert (
        "Tarification" in html
    ), """Price section not found — page may be JS-rendered; consider
    switching fetch_event_page to Playwright"""
