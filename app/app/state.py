import reflex as rx
from .models import (
    EventData,
    EventGroup,
    MovieData,
    MovieGroup,
    SearchResult,
    TodayItem,
)
import itertools
from datetime import date, datetime, timedelta
import psycopg2
import psycopg2.extras
import os
import json
import hashlib
import logging


def _schema_version() -> str:
    """SHA-1 of the cached models' field names — changes when models change,
    invalidating any cached payloads that no longer match the current shape.
    Bump _CACHE_SALT to force-invalidate all client caches without a model change."""
    _CACHE_SALT = "v5"
    fingerprint: dict = {"_salt": _CACHE_SALT}
    for cls in (EventData, MovieData, TodayItem):
        fields = getattr(cls, "model_fields", None) or getattr(cls, "__fields__", {})
        fingerprint[cls.__name__] = sorted(fields.keys())
    payload = json.dumps(fingerprint, sort_keys=True).encode()
    return hashlib.sha1(payload).hexdigest()[:12]


_SCHEMA_VERSION = _schema_version()


def _serialize_models(items: list) -> str:
    out = []
    for item in items:
        d = {k: v for k, v in item.__dict__.items() if not k.startswith("_")}
        for k, v in list(d.items()):
            if hasattr(v, "isoformat"):
                d[k] = v.isoformat()
        out.append(d)
    return json.dumps(out, separators=(",", ":"))


_DATE_FIELDS = {"event_date", "release_date", "display_date"}


def _deserialize_models(s: str, model_cls):
    if not s:
        return []
    try:
        rows = json.loads(s)
        result = []
        for row in rows:
            for field in _DATE_FIELDS:
                if field in row and isinstance(row[field], str) and row[field]:
                    try:
                        row[field] = date.fromisoformat(row[field])
                    except (ValueError, AttributeError):
                        pass
            result.append(model_cls(**row))
        return result
    except Exception as e:
        logging.warning(f"Cache deserialize failed for {model_cls.__name__}: {e}")
        return []


def _score_title(query_lower: str, title: str) -> int:
    t = title.lower()
    if t == query_lower:
        return 100
    if t.startswith(query_lower):
        return 80
    if query_lower in t:
        return 60
    return 0


def _score_location(query_lower: str, location: str) -> int:
    if query_lower in location.lower():
        return 40
    return 0


def _apply_event_filters(
    events: list[EventData],
    selected_family: str,
    selected_city: str,
    selected_price_range: str,
) -> list[EventData]:
    if selected_family != "All":
        events = [e for e in events if e.genre_family == selected_family]
    if selected_city != "All":
        events = [e for e in events if e.city_computed == selected_city]

    if selected_price_range == "Gratuit":
        events = [e for e in events if e.min_price == 0.0]
    elif selected_price_range == "Payant":
        events = [e for e in events if e.price_tag == "payant"]
    elif selected_price_range == "< 10€":
        events = [e for e in events if e.min_price is not None and 0 < e.min_price < 10]
    elif selected_price_range == "10-20€":
        events = [
            e for e in events if e.min_price is not None and 10 <= e.min_price <= 20
        ]
    elif selected_price_range == "20€+":
        events = [e for e in events if e.min_price is not None and e.min_price > 20]
    elif selected_price_range == "Inconnu":
        events = [e for e in events if e.min_price is None and e.price_tag is None]
    return events


def _group_by_date(events: list[EventData]) -> list[EventGroup]:
    if not events:
        return []
    current_year = date.today().year
    sorted_events = sorted(events, key=lambda x: x.event_date)
    res = []
    for date_obj, group in itertools.groupby(sorted_events, key=lambda x: x.event_date):
        if date_obj.year != current_year:
            label = date_obj.strftime("%A %d %B %Y").capitalize()
        else:
            label = date_obj.strftime("%A %d %B").capitalize()
        res.append(EventGroup(date_display=label, events=list(group)))
    return res


_INITIAL_WINDOW_WEEKS = 1
_MORE_WINDOW_WEEKS = 1
_MOVIES_INITIAL_LIMIT = 30
_MOVIES_MORE_LIMIT = 30


class State(rx.State):
    active_tab: str = "concerts"

    # Per-category lists — loaded lazily on tab visit, then cached client-side.
    concerts: list[EventData] = []
    spectacles: list[EventData] = []
    expositions: list[EventData] = []
    movies: list[MovieData] = []
    today_items: list[TodayItem] = []

    # localStorage-backed cache (stale-while-revalidate). Strings store JSON.
    # The version is a hash of the model schema — when a model field changes,
    # _SCHEMA_VERSION changes and all caches are auto-invalidated on next read.
    cache_concerts: str = rx.LocalStorage("")
    cache_spectacles: str = rx.LocalStorage("")
    cache_expositions: str = rx.LocalStorage("")
    cache_movies: str = rx.LocalStorage("")
    cache_today: str = rx.LocalStorage("")
    cache_version: str = rx.LocalStorage("")
    cache_updated_at: str = rx.LocalStorage("")

    # Per-category cursors (event_date upper bound already fetched).
    _concerts_end_date: date = date.today() + timedelta(weeks=_INITIAL_WINDOW_WEEKS)
    _spectacles_end_date: date = date.today() + timedelta(weeks=_INITIAL_WINDOW_WEEKS)

    # First-load gates so we only hit the DB once per category per session.
    concerts_loaded: bool = False
    spectacles_loaded: bool = False
    expositions_loaded: bool = False
    movies_loaded: bool = False
    today_loaded: bool = False

    events_loading: bool = False
    selected_family: str = "All"
    selected_city: str = "All"
    selected_genre: str = "All"
    selected_price_range: str = "Tous"
    selected_today_type: str = "Tous"
    search_query: str = ""
    search_events: list[EventData] = []
    search_movies: list[MovieData] = []
    skills_open: bool = False
    expanded_skill: str = ""

    def toggle_skills(self):
        self.skills_open = not self.skills_open
        if not self.skills_open:
            self.expanded_skill = ""

    def toggle_skill(self, name: str):
        self.expanded_skill = "" if self.expanded_skill == name else name

    def go_today(self):
        return rx.redirect("/")

    def go_concerts(self):
        return rx.redirect("/concerts")

    def go_spectacles(self):
        return rx.redirect("/spectacles")

    def go_expositions(self):
        return rx.redirect("/expositions")

    def go_films(self):
        return rx.redirect("/films")

    def go_about(self):
        return rx.redirect("/about")

    # ---- DB helpers (psycopg2 — avoids SQLAlchemy session expiry) ----

    def _pg(self):
        return psycopg2.connect(os.environ["POSTGRES_URL"])

    def _fetch_category(self, category: str, end_date: date) -> list[EventData]:
        cutoff = date.today() - timedelta(days=1)
        conn = self._pg()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM events WHERE event_date >= %s AND event_date <= %s"
            " AND category = %s ORDER BY event_date",
            (cutoff, end_date, category),
        )
        rows = [EventData(**dict(r)) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return rows

    def _fetch_more_category(
        self, category: str, after: date, until: date
    ) -> list[EventData]:
        conn = self._pg()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM events WHERE event_date > %s AND event_date <= %s"
            " AND category = %s ORDER BY event_date",
            (after, until, category),
        )
        rows = [EventData(**dict(r)) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return rows

    def _fetch_movies(self, limit: int, after_date=None) -> list[MovieData]:
        cutoff = date.today() - timedelta(days=1)
        conn = self._pg()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if after_date is not None:
            cur.execute(
                "SELECT * FROM movies WHERE release_date > %s"
                " ORDER BY release_date LIMIT %s",
                (after_date, limit),
            )
        else:
            cur.execute(
                "SELECT * FROM movies WHERE release_date >= %s"
                " ORDER BY release_date LIMIT %s",
                (cutoff, limit),
            )
        rows = [MovieData(**dict(r)) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return rows

    # ---- Cache helpers ----

    def _hydrate_from_cache(self, cached_str: str, model_cls):
        """Returns deserialized list, or None on miss / version mismatch."""
        if not cached_str:
            return None
        if self.cache_version != _SCHEMA_VERSION:
            # Schema drifted since this cache was written — drop everything.
            self._invalidate_caches()
            return None
        items = _deserialize_models(cached_str, model_cls)
        return items or None

    def _invalidate_caches(self):
        self.cache_concerts = ""
        self.cache_spectacles = ""
        self.cache_expositions = ""
        self.cache_movies = ""
        self.cache_today = ""
        self.cache_version = ""
        self.cache_updated_at = ""

    def _write_concerts_cache(self):
        self.cache_concerts = _serialize_models(self.concerts)
        self.cache_version = _SCHEMA_VERSION
        self.cache_updated_at = datetime.utcnow().isoformat()

    def _write_spectacles_cache(self):
        self.cache_spectacles = _serialize_models(self.spectacles)
        self.cache_version = _SCHEMA_VERSION
        self.cache_updated_at = datetime.utcnow().isoformat()

    def _write_expositions_cache(self):
        self.cache_expositions = _serialize_models(self.expositions)
        self.cache_version = _SCHEMA_VERSION
        self.cache_updated_at = datetime.utcnow().isoformat()

    def _write_movies_cache(self):
        self.cache_movies = _serialize_models(self.movies)
        self.cache_version = _SCHEMA_VERSION
        self.cache_updated_at = datetime.utcnow().isoformat()

    def _write_today_cache(self):
        self.cache_today = _serialize_models(self.today_items)
        self.cache_version = _SCHEMA_VERSION
        self.cache_updated_at = datetime.utcnow().isoformat()

    # ---- Cache freshness ----

    _CACHE_MAX_AGE_SECONDS = 3600  # 1h — use cache if newer than this, else refetch

    def _cache_age_seconds(self) -> int:
        if not self.cache_updated_at:
            return -1
        try:
            ts = datetime.fromisoformat(self.cache_updated_at)
            return int((datetime.utcnow() - ts).total_seconds())
        except Exception:
            return -1

    def _cache_is_fresh(self) -> bool:
        age = self._cache_age_seconds()
        return 0 <= age < self._CACHE_MAX_AGE_SECONDS

    # ---- Synchronous ensure helpers (fetch + cache write, idempotent) ----
    # Fail-soft: any DB error sets the loaded flag anyway so the skeleton
    # never gets stuck. We log but never surface errors to the user.

    def _ensure_concerts(self):
        if self.concerts_loaded:
            return
        try:
            self._concerts_end_date = date.today() + timedelta(
                weeks=_INITIAL_WINDOW_WEEKS
            )
            self.concerts = self._fetch_category("concerts", self._concerts_end_date)
            self._write_concerts_cache()
        except Exception as e:
            logging.warning(f"_ensure_concerts: {e}")
        finally:
            self.concerts_loaded = True

    def _ensure_spectacles(self):
        if self.spectacles_loaded:
            return
        try:
            self._spectacles_end_date = date.today() + timedelta(
                weeks=_INITIAL_WINDOW_WEEKS
            )
            self.spectacles = self._fetch_category(
                "spectacles", self._spectacles_end_date
            )
            self._write_spectacles_cache()
        except Exception as e:
            logging.warning(f"_ensure_spectacles: {e}")
        finally:
            self.spectacles_loaded = True

    def _ensure_expositions(self):
        if self.expositions_loaded:
            return
        try:
            cutoff = date.today() - timedelta(days=1)
            conn = self._pg()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                "SELECT DISTINCT ON (title, location) * FROM events"
                " WHERE event_date >= %s AND category = 'expositions'"
                " ORDER BY title, location, event_date",
                (cutoff,),
            )
            events = [EventData(**dict(r)) for r in cur.fetchall()]
            cur.close()
            conn.close()
            self.expositions = sorted(events, key=lambda e: e.event_date)
            self._write_expositions_cache()
        except Exception as e:
            logging.warning(f"_ensure_expositions: {e}")
        finally:
            self.expositions_loaded = True

    def _ensure_movies(self):
        if self.movies_loaded:
            return
        try:
            self.movies = self._fetch_movies(_MOVIES_INITIAL_LIMIT)
            self._write_movies_cache()
        except Exception as e:
            logging.warning(f"_ensure_movies: {e}")
        finally:
            self.movies_loaded = True

    def _ensure_today(self):
        if self.today_loaded:
            return
        try:
            self._load_today()
            self._write_today_cache()
        except Exception as e:
            logging.warning(f"_ensure_today: {e}")
        finally:
            self.today_loaded = True

    # ---- Page on_load handlers ----
    # Sync only. Pattern: if a fresh-enough localStorage cache exists, use it
    # and skip the DB hit entirely. Otherwise re-fetch and write the cache.
    # No async generators (Reflex 0.8.x async-gen support is brittle).

    def on_load_today(self):
        self.active_tab = "today"
        if self.today_loaded:
            return
        cached = self._hydrate_from_cache(self.cache_today, TodayItem)
        if cached and self._cache_is_fresh():
            self.today_items = cached
            self.today_loaded = True
            return
        if cached:
            # Use stale cache as a placeholder so skeleton doesn't show
            self.today_items = cached
        self._ensure_today()

    def on_load_concerts(self):
        self.active_tab = "concerts"
        if self.concerts_loaded:
            return
        cached = self._hydrate_from_cache(self.cache_concerts, EventData)
        if cached and self._cache_is_fresh():
            self.concerts = cached
            self._concerts_end_date = max(
                (e.event_date for e in cached),
                default=date.today() + timedelta(weeks=_INITIAL_WINDOW_WEEKS),
            )
            self.concerts_loaded = True
            return
        if cached:
            self.concerts = cached
        self._ensure_concerts()

    def on_load_spectacles(self):
        self.active_tab = "spectacles"
        if self.spectacles_loaded:
            return
        cached = self._hydrate_from_cache(self.cache_spectacles, EventData)
        if cached and self._cache_is_fresh():
            self.spectacles = cached
            self._spectacles_end_date = max(
                (e.event_date for e in cached),
                default=date.today() + timedelta(weeks=_INITIAL_WINDOW_WEEKS),
            )
            self.spectacles_loaded = True
            return
        if cached:
            self.spectacles = cached
        self._ensure_spectacles()

    def on_load_expositions(self):
        self.active_tab = "expositions"
        if self.expositions_loaded:
            return
        cached = self._hydrate_from_cache(self.cache_expositions, EventData)
        if cached and self._cache_is_fresh():
            self.expositions = cached
            self.expositions_loaded = True
            return
        if cached:
            self.expositions = cached
        self._ensure_expositions()

    def on_load_about(self):
        self.active_tab = "about"

    def on_load_films(self):
        self.active_tab = "films"
        if self.movies_loaded:
            return
        cached = self._hydrate_from_cache(self.cache_movies, MovieData)
        if cached and self._cache_is_fresh():
            self.movies = cached
            self.movies_loaded = True
            return
        if cached:
            self.movies = cached
        self._ensure_movies()

    # ---- Setters ----

    def set_family(self, value: str):
        self.selected_family = value

    def set_city(self, value: str):
        self.selected_city = value

    def set_genre(self, value: str):
        self.selected_genre = value

    def set_price_range(self, value: str):
        self.selected_price_range = value

    def set_today_type(self, value: str):
        self.selected_today_type = value

    def _search_db(self, query: str) -> None:
        q = f"%{query}%"
        cutoff = date.today() - timedelta(days=1)
        try:
            conn = self._pg()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                "SELECT * FROM events WHERE event_date >= %s"
                " AND (title ILIKE %s OR location ILIKE %s) ORDER BY event_date",
                (cutoff, q, q),
            )
            self.search_events = [EventData(**dict(r)) for r in cur.fetchall()]
            cur.execute(
                "SELECT * FROM movies WHERE release_date >= %s"
                " AND title ILIKE %s ORDER BY release_date",
                (cutoff, q),
            )
            self.search_movies = [MovieData(**dict(r)) for r in cur.fetchall()]
            cur.close()
            conn.close()
        except Exception as e:
            logging.warning(f"_search_db: {e}")

    def set_search(self, value: str):
        self.search_query = value
        q = value.strip()
        if len(q) >= 2:
            self._search_db(q)
        else:
            self.search_events = []
            self.search_movies = []

    # ---- Load-more (IntersectionObserver-triggered) ----

    def load_more_events(self):
        if self.events_loading or self.search_query.strip():
            return
        self.events_loading = True
        tab = self.active_tab
        if tab == "concerts":
            new_end = self._concerts_end_date + timedelta(weeks=_MORE_WINDOW_WEEKS)
            more = self._fetch_more_category(
                "concerts", self._concerts_end_date, new_end
            )
            if more:
                self.concerts = self.concerts + more
                self._write_concerts_cache()
            self._concerts_end_date = new_end
        elif tab == "spectacles":
            new_end = self._spectacles_end_date + timedelta(weeks=_MORE_WINDOW_WEEKS)
            more = self._fetch_more_category(
                "spectacles", self._spectacles_end_date, new_end
            )
            if more:
                self.spectacles = self.spectacles + more
                self._write_spectacles_cache()
            self._spectacles_end_date = new_end
        elif tab == "expositions":
            # Expositions are fully loaded upfront via DISTINCT ON — no paging.
            pass
        elif tab == "films":
            last_date = self.movies[-1].release_date if self.movies else None
            if last_date is not None:
                more_movies = self._fetch_movies(
                    _MOVIES_MORE_LIMIT, after_date=last_date
                )
                if more_movies:
                    self.movies = self.movies + more_movies
                    self._write_movies_cache()
        self.events_loading = False

    # ---- Today (fct_today materialised view) ----

    def _load_today(self) -> None:
        try:
            conn = psycopg2.connect(os.environ["POSTGRES_URL"])
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM fct_today ORDER BY item_type, title")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            self.today_items = [
                TodayItem(
                    item_type=row["item_type"],
                    title=row["title"],
                    display_date=row["display_date"],
                    category=row["category"],
                    event_type=row["event_type"],
                    genre_family=row["genre_family"],
                    location=row["location"],
                    city_computed=row["city_computed"],
                    source_url=row["source_url"],
                    url_billetterie=row["url_billetterie"],
                    min_price=(
                        float(row["min_price"])
                        if row["min_price"] is not None
                        else None
                    ),
                    max_price=(
                        float(row["max_price"])
                        if row["max_price"] is not None
                        else None
                    ),
                    free_label=row["free_label"],
                    price_tag=row["price_tag"],
                    genres=row["genres"],
                    director=row["director"],
                    synopsis=row["synopsis"],
                    duration=row["duration"],
                    movie_url=row["movie_url"],
                )
                for row in rows
            ]
        except Exception as e:
            logging.warning(f"Could not load fct_today: {e}")
            self.today_items = []

    # ---- Computed vars ----

    @rx.var
    def current_events(self) -> list[EventData]:
        if self.active_tab == "spectacles":
            return self.spectacles
        if self.active_tab == "expositions":
            return self.expositions
        return self.concerts

    @rx.var
    def unique_families(self) -> list[str]:
        families = sorted(
            set(e.genre_family for e in self.current_events if e.genre_family)
        )
        return ["All"] + families

    @rx.var
    def unique_cities(self) -> list[str]:
        cities = sorted(
            set(
                e.city_computed
                for e in self.current_events
                if e.city_computed and e.city_computed != "Autre"
            )
        )
        return ["All"] + cities

    @rx.var
    def unique_genres(self) -> list[str]:
        genres = set()
        for m in self.movies:
            if m.genres:
                for g in m.genres.replace(" | ", ",").split(","):
                    genre = g.strip()
                    if genre:
                        genres.add(genre)
        return ["All"] + sorted(genres)

    @rx.var
    def grouped_events_list(self) -> list[EventGroup]:
        today = date.today()
        filtered = [
            e for e in self.concerts if e.event_date >= today - timedelta(days=1)
        ]
        filtered = _apply_event_filters(
            filtered,
            self.selected_family,
            self.selected_city,
            self.selected_price_range,
        )
        return _group_by_date(filtered)

    @rx.var
    def grouped_spectacles_list(self) -> list[EventGroup]:
        today = date.today()
        filtered = [
            e for e in self.spectacles if e.event_date >= today - timedelta(days=1)
        ]
        filtered = _apply_event_filters(
            filtered,
            self.selected_family,
            self.selected_city,
            self.selected_price_range,
        )
        return _group_by_date(filtered)

    @rx.var
    def grouped_expositions_list(self) -> list[EventGroup]:
        # Expositions are multi-day: the scraper writes one row per showtime.
        # Dedup by (title, location) keeping only the nearest future date.
        today = date.today()
        filtered = [
            e for e in self.expositions if e.event_date >= today - timedelta(days=1)
        ]
        filtered = _apply_event_filters(
            filtered,
            self.selected_family,
            self.selected_city,
            self.selected_price_range,
        )
        seen: dict = {}
        for e in sorted(filtered, key=lambda x: x.event_date):
            key = (e.title, e.location or "")
            if key not in seen:
                seen[key] = e
        return _group_by_date(list(seen.values()))

    @rx.var
    def grouped_movies_list(self) -> list[MovieGroup]:
        if not self.movies:
            return []
        current_year = date.today().year

        filtered = self.movies
        if self.selected_genre != "All":
            filtered = [
                m for m in filtered if m.genres and self.selected_genre in m.genres
            ]

        res = []
        for date_obj, group in itertools.groupby(
            [m for m in filtered if m.release_date],
            key=lambda m: m.release_date,
        ):
            if date_obj.year != current_year:
                label = date_obj.strftime("%A %d %B %Y").capitalize()
            else:
                label = date_obj.strftime("%A %d %B").capitalize()
            res.append(MovieGroup(date_display=label, movies=list(group)))
        return res

    @rx.var
    def search_results(self) -> list[SearchResult]:
        if not self.search_query.strip():
            return []
        q = self.search_query.lower().strip()
        results = []
        for event in self.search_events:
            score = max(
                _score_title(q, event.title),
                _score_location(q, event.location or ""),
                _score_location(q, event.city_computed or ""),
                40,  # DB ILIKE already matched — floor at 40
            )
            results.append(
                SearchResult(
                    type=event.category or "event",
                    title=event.title,
                    score=score,
                    event=event,
                )
            )
        for movie in self.search_movies:
            score = max(_score_title(q, movie.title), 40)
            results.append(
                SearchResult(
                    type="movie",
                    title=movie.title,
                    score=score,
                    movie=movie,
                )
            )
        results.sort(key=lambda x: (-x.score, x.title))
        return results

    @rx.var
    def has_price_data(self) -> bool:
        return any(
            e.min_price is not None or e.price_tag is not None
            for e in self.current_events
        )

    @rx.var
    def today_types_available(self) -> list[str]:
        types = set()
        for item in self.today_items:
            if item.item_type == "movie":
                types.add("Films")
            elif item.category == "spectacles":
                types.add("Spectacles")
            elif item.category == "expositions":
                types.add("Expos")
            else:
                types.add("Concerts")
        return ["Tous"] + sorted(types)

    def _today_filter_keep(self, section_name: str) -> bool:
        return self.selected_today_type in ("Tous", section_name)

    @rx.var
    def today_concerts(self) -> list[TodayItem]:
        if not self._today_filter_keep("Concerts"):
            return []
        return [
            i
            for i in self.today_items
            if i.item_type == "event" and i.category == "concerts"
        ]

    @rx.var
    def today_spectacles(self) -> list[TodayItem]:
        if not self._today_filter_keep("Spectacles"):
            return []
        return [i for i in self.today_items if i.category == "spectacles"]

    @rx.var
    def today_expos(self) -> list[TodayItem]:
        if not self._today_filter_keep("Expos"):
            return []
        return [i for i in self.today_items if i.category == "expositions"]

    @rx.var
    def today_movies(self) -> list[TodayItem]:
        if not self._today_filter_keep("Films"):
            return []
        return [i for i in self.today_items if i.item_type == "movie"]

    @rx.var
    def has_multiple_families(self) -> bool:
        return len(self.unique_families) > 1

    @rx.var
    def has_multiple_cities(self) -> bool:
        return len(self.unique_cities) > 1

    @rx.var
    def has_multiple_genres(self) -> bool:
        return len(self.unique_genres) > 1

    @rx.var
    def has_multiple_today_types(self) -> bool:
        return len(self.today_types_available) > 1

    # Per-tab "show skeleton" flags — true only on the very first visit when
    # neither in-memory state nor localStorage cache has any data yet.
    @rx.var
    def today_loading(self) -> bool:
        return not self.today_loaded and not self.today_items

    @rx.var
    def concerts_loading(self) -> bool:
        return not self.concerts_loaded and not self.concerts

    @rx.var
    def spectacles_loading(self) -> bool:
        return not self.spectacles_loaded and not self.spectacles

    @rx.var
    def expositions_loading(self) -> bool:
        return not self.expositions_loaded and not self.expositions

    @rx.var
    def films_loading(self) -> bool:
        return not self.movies_loaded and not self.movies
