import reflex as rx
from typing import Optional, List
import sqlmodel
from datetime import date
from pydantic import BaseModel


class Event(rx.Model, table=True):  # type: ignore
    __tablename__ = "events"

    id: Optional[int] = sqlmodel.Field(default=None, primary_key=True)
    source: str
    title: str
    event_type: str
    event_date: date
    location: Optional[str]
    city_computed: Optional[str]
    url_billetterie: Optional[str]
    genre_family: Optional[str] = None
    raw_id: str
    source_url: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    free_label: Optional[str] = None
    price_tag: Optional[str] = None
    category: Optional[str] = "concerts"


class EventPrice(rx.Model, table=True):  # type: ignore
    __tablename__ = "event_prices"

    id: Optional[int] = sqlmodel.Field(default=None, primary_key=True)
    event_signature: str
    label: str
    amount: float


class EventGroup(BaseModel):
    date_display: str
    events: List[Event]


class Movie(rx.Model, table=True):  # type: ignore
    __tablename__ = "movies"

    id: Optional[int] = sqlmodel.Field(default=None, primary_key=True)
    title: str
    director: Optional[str] = None
    producer: Optional[str] = None
    genres: Optional[str] = None
    synopsis: Optional[str] = None
    release_date: Optional[date] = None
    duration: Optional[str] = None
    url: Optional[str] = None


class MovieGroup(BaseModel):
    date_display: str
    movies: List[Movie]


class SearchResult(BaseModel):
    type: str  # "event" or "movie"
    title: str
    score: int
    event: Optional[Event] = None
    movie: Optional[Movie] = None


class TodayItem(BaseModel):
    item_type: str
    title: str
    display_date: Optional[date] = None
    category: Optional[str] = None
    event_type: Optional[str] = None
    genre_family: Optional[str] = None
    location: Optional[str] = None
    city_computed: Optional[str] = None
    source_url: Optional[str] = None
    url_billetterie: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    free_label: Optional[str] = None
    price_tag: Optional[str] = None
    genres: Optional[str] = None
    director: Optional[str] = None
    synopsis: Optional[str] = None
    duration: Optional[str] = None
    movie_url: Optional[str] = None
