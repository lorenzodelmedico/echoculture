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
    raw_id: str


class EventGroup(BaseModel):
    date_display: str
    events: List[Event]
