import reflex as rx
from .models import Event, EventGroup, Movie, MovieGroup, SearchResult, TodayItem
from sqlmodel import select, col
import itertools
from datetime import date, timedelta
import psycopg2
import psycopg2.extras
import os


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


def _filter_and_group_events(
    events: list[Event],
    category: str,
    selected_family: str,
    selected_city: str,
    selected_price_range: str,
) -> list[EventGroup]:
    if not events:
        return []

    today = date.today()
    current_year = today.year

    filtered = [
        e
        for e in events
        if e.event_date >= today - timedelta(days=1) and e.category == category
    ]
    if selected_family != "All":
        filtered = [e for e in filtered if e.genre_family == selected_family]
    if selected_city != "All":
        filtered = [e for e in filtered if e.city_computed == selected_city]

    if selected_price_range == "Gratuit":
        filtered = [e for e in filtered if e.min_price == 0.0]
    elif selected_price_range == "Payant":
        filtered = [e for e in filtered if e.price_tag == "payant"]
    elif selected_price_range == "< 10\u20ac":
        filtered = [
            e for e in filtered if e.min_price is not None and 0 < e.min_price < 10
        ]
    elif selected_price_range == "10-20\u20ac":
        filtered = [
            e for e in filtered if e.min_price is not None and 10 <= e.min_price <= 20
        ]
    elif selected_price_range == "20\u20ac+":
        filtered = [e for e in filtered if e.min_price is not None and e.min_price > 20]
    elif selected_price_range == "Inconnu":
        filtered = [e for e in filtered if e.min_price is None and e.price_tag is None]

    sorted_events = sorted(filtered, key=lambda x: x.event_date)

    res = []
    for date_obj, group in itertools.groupby(sorted_events, key=lambda x: x.event_date):
        if date_obj.year != current_year:
            label = date_obj.strftime("%A %d %B %Y").capitalize()
        else:
            label = date_obj.strftime("%A %d %B").capitalize()
        res.append(EventGroup(date_display=label, events=list(group)))
    return res


_INITIAL_WINDOW_WEEKS = 2
_MORE_WINDOW_WEEKS = 3


class State(rx.State):
    active_tab: str = "concerts"
    events: list[Event] = []
    movies: list[Movie] = []
    today_items: list[TodayItem] = []
    _events_end_date: date = date.today() + timedelta(weeks=_INITIAL_WINDOW_WEEKS)
    events_loading: bool = False
    selected_family: str = "All"
    selected_city: str = "All"
    selected_genre: str = "All"
    selected_price_range: str = "Tous"
    selected_today_type: str = "All"
    search_query: str = ""

    def set_tab(self, tab: str):
        self.active_tab = tab

    def go_today(self):
        self.active_tab = "today"
        return rx.redirect("/")

    def go_concerts(self):
        self.active_tab = "concerts"
        return rx.redirect("/")

    def go_spectacles(self):
        self.active_tab = "spectacles"
        return rx.redirect("/")

    def go_expositions(self):
        self.active_tab = "expositions"
        return rx.redirect("/")

    def go_films(self):
        self.active_tab = "films"
        return rx.redirect("/")

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

    def set_search(self, value: str):
        self.search_query = value

    def load_events(self):
        cutoff = date.today() - timedelta(days=1)
        self._events_end_date = date.today() + timedelta(weeks=_INITIAL_WINDOW_WEEKS)
        with rx.session() as session:
            self.events = session.exec(
                select(Event)
                .where(col(Event.event_date) >= cutoff)
                .where(col(Event.event_date) <= self._events_end_date)
                .order_by(Event.event_date)
            ).all()
            self.movies = session.exec(
                select(Movie)
                .where(col(Movie.release_date) >= cutoff)
                .order_by(Movie.release_date)
            ).all()

    def load_more_events(self):
        if self.events_loading:
            return
        self.events_loading = True
        new_end = self._events_end_date + timedelta(weeks=_MORE_WINDOW_WEEKS)
        with rx.session() as session:
            more = session.exec(
                select(Event)
                .where(col(Event.event_date) > self._events_end_date)
                .where(col(Event.event_date) <= new_end)
                .order_by(Event.event_date)
            ).all()
        self.events = self.events + more
        self._events_end_date = new_end
        self.events_loading = False

        # Load today's unified view from the dbt mart
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
            import logging

            logging.warning(f"Could not load fct_today: {e}")
            self.today_items = []

    @rx.var
    def unique_families(self) -> list[str]:
        cat = self.active_tab
        families = sorted(
            list(
                set(
                    e.genre_family
                    for e in self.events
                    if e.genre_family and e.category == cat
                )
            )
        )
        return ["All"] + families

    @rx.var
    def unique_cities(self) -> list[str]:
        cat = self.active_tab
        cities = sorted(
            list(
                set(
                    e.city_computed
                    for e in self.events
                    if e.city_computed
                    and e.city_computed != "Autre"
                    and e.category == cat
                )
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
        return ["All"] + sorted(list(genres))

    @rx.var
    def grouped_events_list(self) -> list[EventGroup]:
        return _filter_and_group_events(
            self.events,
            "concerts",
            self.selected_family,
            self.selected_city,
            self.selected_price_range,
        )

    @rx.var
    def grouped_spectacles_list(self) -> list[EventGroup]:
        return _filter_and_group_events(
            self.events,
            "spectacles",
            self.selected_family,
            self.selected_city,
            self.selected_price_range,
        )

    @rx.var
    def grouped_expositions_list(self) -> list[EventGroup]:
        return _filter_and_group_events(
            self.events,
            "expositions",
            self.selected_family,
            self.selected_city,
            self.selected_price_range,
        )

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

        query_lower = self.search_query.lower().strip()
        results = []

        for event in self.events:
            score = max(
                _score_title(query_lower, event.title),
                _score_location(query_lower, event.location or ""),
                _score_location(query_lower, event.city_computed or ""),
            )
            if score > 0:
                results.append(
                    SearchResult(
                        type=event.category or "event",
                        title=event.title,
                        score=score,
                        event=event,
                    )
                )

        for movie in self.movies:
            score = _score_title(query_lower, movie.title)
            if score > 0:
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
            e.min_price is not None or e.price_tag is not None for e in self.events
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
        return ["All"] + sorted(types)

    @rx.var
    def filtered_today_items(self) -> list[TodayItem]:
        if self.selected_today_type == "All":
            return self.today_items
        t = self.selected_today_type
        return [
            i
            for i in self.today_items
            if (t == "Films" and i.item_type == "movie")
            or (t == "Spectacles" and i.category == "spectacles")
            or (t == "Expos" and i.category == "expositions")
            or (t == "Concerts" and i.item_type == "event" and i.category == "concerts")
        ]

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
