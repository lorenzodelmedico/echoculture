import reflex as rx
from .models import Event, EventGroup, Movie, MovieGroup, SearchResult
from sqlmodel import select
import itertools
from datetime import date, timedelta


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


class State(rx.State):
    active_tab: str = "concerts"  # "concerts" | "films"
    events: list[Event] = []
    movies: list[Movie] = []
    selected_family: str = "All"
    selected_city: str = "All"
    selected_genre: str = "All"
    selected_price_range: str = "Tous"
    search_query: str = ""

    def set_tab(self, tab: str):
        self.active_tab = tab

    def go_concerts(self):
        self.active_tab = "concerts"
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

    def set_search(self, value: str):
        self.search_query = value

    def load_events(self):
        with rx.session() as session:
            self.events = session.exec(select(Event).order_by(Event.event_date)).all()
            self.movies = session.exec(select(Movie).order_by(Movie.release_date)).all()

    @rx.var
    def unique_families(self) -> list[str]:
        families = sorted(
            list(set(e.genre_family for e in self.events if e.genre_family))
        )
        return ["All"] + families

    @rx.var
    def unique_cities(self) -> list[str]:
        cities = sorted(
            list(
                set(
                    e.city_computed
                    for e in self.events
                    if e.city_computed and e.city_computed != "Autre"
                )
            )
        )
        return ["All"] + cities

    @rx.var
    def unique_genres(self) -> list[str]:
        genres = set()
        for m in self.movies:
            if m.genres:
                # Handle comma or pipe-separated genres
                for g in m.genres.replace(" | ", ",").split(","):
                    genre = g.strip()
                    if genre:
                        genres.add(genre)
        return ["All"] + sorted(list(genres))

    @rx.var
    def grouped_events_list(self) -> list[EventGroup]:
        if not self.events:
            return []

        today = date.today()
        current_year = today.year

        filtered = [e for e in self.events if e.event_date >= today - timedelta(days=1)]
        if self.selected_family != "All":
            filtered = [e for e in filtered if e.genre_family == self.selected_family]
        if self.selected_city != "All":
            filtered = [e for e in filtered if e.city_computed == self.selected_city]

        if self.selected_price_range == "Gratuit":
            filtered = [e for e in filtered if e.min_price == 0.0]
        elif self.selected_price_range == "< 10€":
            filtered = [
                e for e in filtered if e.min_price is not None and e.min_price < 10
            ]
        elif self.selected_price_range == "10-20€":
            filtered = [
                e
                for e in filtered
                if e.min_price is not None and 10 <= e.min_price <= 20
            ]
        elif self.selected_price_range == "20€+":
            filtered = [
                e for e in filtered if e.min_price is not None and e.min_price > 20
            ]

        sorted_events = sorted(filtered, key=lambda x: x.event_date)

        res = []
        for date_obj, group in itertools.groupby(
            sorted_events, key=lambda x: x.event_date
        ):
            # Add year to the label only when the event is not in the current year
            if date_obj.year != current_year:
                label = date_obj.strftime("%A %d %B %Y").capitalize()
            else:
                label = date_obj.strftime("%A %d %B").capitalize()
            res.append(
                EventGroup(
                    date_display=label,
                    events=list(group),
                )
            )
        return res

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
                        type="event",
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
        return any(e.min_price is not None for e in self.events)
