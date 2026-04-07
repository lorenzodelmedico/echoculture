import reflex as rx
from .models import Event, EventGroup  # On garde tes imports
from sqlmodel import select
import itertools


class State(rx.State):
    events: list[Event] = []
    selected_type: str = "All"

    def set_type(self, value: str):
        self.selected_type = value

    def load_events(self):
        with rx.session() as session:
            statement = select(Event).order_by(Event.event_date)
            self.events = session.exec(statement).all()

    @rx.var
    def unique_types(self) -> list[str]:
        """Génère la liste des filtres dynamiquement depuis la DB."""
        # On extrait les types, on enlève les doublons et on trie
        db_types = sorted(list(set(e.event_type for e in self.events)))
        return ["All"] + db_types

    @rx.var
    def grouped_events_list(self) -> list[EventGroup]:
        if not self.events:
            return []

        filtered = (
            self.events
            if self.selected_type == "All"
            else [e for e in self.events if e.event_type == self.selected_type]
        )

        sorted_events = sorted(filtered, key=lambda x: x.event_date)

        res = []
        for date_obj, group in itertools.groupby(
            sorted_events, key=lambda x: x.event_date
        ):
            res.append(
                EventGroup(
                    date_display=date_obj.strftime("%A %d %B").capitalize(),
                    events=list(group),
                )
            )
        return res
