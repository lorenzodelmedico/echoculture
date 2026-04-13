import pytest
from scrapers.ecrantotal_pipeline import _extract_genres, fetch_wikipedia_genres

# ---------------------------------------------------------------------------
# Unit tests — no network, pure extraction logic
# ---------------------------------------------------------------------------


def test_categories_zelda():
    cats = ["2020s fantasy adventure films", "American fantasy adventure films"]
    result = _extract_genres(cats, "")
    assert result is not None
    assert "Fantasy" in result
    assert "Adventure" in result


def test_categories_inception():
    cats = ["2010 action thriller films", "2010 science fiction action films"]
    result = _extract_genres(cats, "")
    assert result is not None
    assert "Action" in result
    assert "Thriller" in result
    assert "Science Fiction" in result


def test_intro_fallback_zelda():
    intro = (
        "The Legend of Zelda is an upcoming fantasy adventure film "
        "based on the video game series by Nintendo."
    )
    result = _extract_genres([], intro)
    assert result is not None
    assert "Fantasy" in result
    assert "Adventure" in result


def test_intro_fallback_inception():
    intro = """Inception is a 2010 science fiction action film written
    and directed by Christopher Nolan."""
    result = _extract_genres([], intro)
    assert result is not None
    assert "Science Fiction" in result
    assert "Action" in result


def test_categories_beat_intro():
    cats = ["2010 action thriller films"]
    intro = "is a drama film"
    result = _extract_genres(cats, intro)
    assert result is not None
    assert "Action" in result
    assert "Thriller" in result
    assert "Drama" not in result


def test_non_film_categories_ignored():
    cats = [
        "English-language films",
        "Films set in New York City",
        "2010 action thriller films",
    ]
    result = _extract_genres(cats, "")
    assert result is not None
    assert "Action" in result
    assert "Thriller" in result


def test_no_match_returns_none():
    result = _extract_genres([], "A story about something interesting.")
    assert result is None


def test_empty_inputs():
    assert _extract_genres([], "") is None


def test_deduplication():
    cats = [
        "2010 action films",
        "2010 action thriller films",
    ]
    result = _extract_genres(cats, "")
    assert result is not None
    assert result.count("Action") == 1


# ---------------------------------------------------------------------------
# Integration tests — hit real Wikipedia API, opt-in only
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_fetch_zelda_genres():
    result = fetch_wikipedia_genres("The Legend of Zelda")
    assert result is not None, "Expected genres for The Legend of Zelda, got None"
    assert any(
        g in result for g in ["Fantasy", "Adventure"]
    ), f"Unexpected genres: {result}"


@pytest.mark.integration
def test_fetch_inception_genres():
    result = fetch_wikipedia_genres("Inception")
    assert result is not None, "Expected genres for Inception, got None"
    assert any(
        g in result for g in ["Science Fiction", "Action", "Thriller"]
    ), f"Unexpected genres: {result}"


@pytest.mark.integration
def test_fetch_french_only_title():
    result = fetch_wikipedia_genres("Sans un bruit")
    assert (
        result is not None
    ), "Expected genres for Sans un bruit (A Quiet Place), got None"
