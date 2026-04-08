import reflex as rx
from .state import State
from .models import Event


def event_card(ev: Event):
    return rx.hstack(
        # Timeline dot
        rx.box(
            width="10px",
            height="10px",
            border_radius="50%",
            bg="accent.9",
            margin_top="6px",
            flex_shrink="0",
        ),
        # Card content
        rx.card(
            rx.vstack(
                # Top row
                rx.hstack(
                    rx.badge(ev.event_type, variant="soft", color_scheme="purple"),
                    rx.spacer(),
                    rx.text(ev.source, size="1", color="gray"),
                    width="100%",
                ),
                # Title
                rx.heading(
                    ev.title,
                    size="4",
                ),
                # Location
                rx.hstack(
                    rx.icon("map-pin", size=14),
                    rx.cond(
                        ev.location,
                        rx.link(
                            rx.text(
                                ev.location,
                                size="2",
                                color_scheme="blue",
                                text_decoration="underline",
                            ),
                            href="https://www.google.com/maps/search/?api=1&query="
                            + rx.Var.create(ev.location).to(str),
                            is_external=True,
                        ),
                        rx.text("Lieu inconnu", size="2", color="gray"),
                    ),
                    spacing="2",
                ),
                spacing="2",
                align_items="start",
            ),
            width="100%",
            variant="surface",
        ),
        width="100%",
        spacing="3",
        align_items="start",
    )


def index() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading("EchoCulture", size="9", weight="bold", margin_y="1em"),
            rx.hstack(
                rx.text("Filtrer par :", size="4", color_scheme="gray"),
                rx.select(
                    State.unique_types,  # Dynamique depuis la DB
                    value=State.selected_type,
                    on_change=State.set_type,
                    variant="surface",
                ),
                rx.button(
                    rx.icon("refresh-cw", size=8),
                    on_click=State.load_events,
                    variant="ghost",
                ),
                align_items="start",
                margin_y="2em",
                width="100%",
            ),
            rx.vstack(
                rx.foreach(
                    State.grouped_events_list,
                    lambda day: rx.vstack(
                        rx.heading(
                            day.date_display, size="5", color="gray", margin_top="2em"
                        ),
                        rx.vstack(
                            rx.foreach(day.events, event_card),
                            spacing="4",
                            width="100%",
                        ),
                        width="100%",
                        align_items="start",
                    ),
                ),
                width="100%",
                border_left="2px solid var(--gray-6)",
                padding_left="1.5em",
                margin_left="0.5em",
            ),
            align_items="start",
            max_width="600px",
            padding_bottom="5em",
        ),
        on_mount=State.load_events,
    )


app = rx.App(
    theme=rx.theme(appearance="dark", accent_color="violet"),
    head_components=[
        # PWA manifest
        rx.el.link(rel="manifest", href="/manifest.json"),
        # Theme
        rx.el.meta(name="theme-color", content="#000000"),
        # iOS support
        rx.el.meta(name="apple-mobile-web-app-capable", content="yes"),
        rx.el.meta(
            name="apple-mobile-web-app-status-bar-style", content="black-translucent"
        ),
        rx.el.meta(name="apple-mobile-web-app-title", content="EchoCulture"),
        # Viewport
        rx.el.meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        # Icons
        rx.el.link(rel="apple-touch-icon", href="/icon-192.png"),
        # Register service worker
        rx.el.script("""
            if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js');
            }
        """),
    ],
)
app.add_page(index)
