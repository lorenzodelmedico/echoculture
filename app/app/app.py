import reflex as rx
from .state import State
from .models import Event, Movie


def event_card(ev: Event):
    return rx.box(
        # Card shell — full height flex column so button is always at bottom
        rx.vstack(
            # Top section: grows to fill available space
            rx.vstack(
                rx.badge(
                    ev.event_type, variant="soft", color_scheme="violet", radius="full"
                ),
                rx.text(ev.title, size="3", weight="bold", color="white"),
                rx.cond(
                    ev.location,
                    rx.link(
                        rx.hstack(
                            rx.icon("map-pin", size=13, color="gray"),
                            rx.text(ev.location, size="2", color="gray"),
                            spacing="1",
                            align_items="center",
                        ),
                        href="https://www.google.com/maps/search/"  # type: ignore
                        + ev.location
                        + "+"
                        + rx.cond(  # type: ignore
                            ev.city_computed,
                            ev.city_computed,
                            "Bordeaux",
                        ),
                        is_external=True,
                        _hover={"opacity": "0.7"},
                    ),
                    rx.hstack(
                        rx.icon("map-pin", size=13, color="gray"),
                        rx.text("Lieu inconnu", size="2", color="gray"),
                        spacing="1",
                        align_items="center",
                    ),
                ),
                spacing="2",
                align_items="start",
                width="100%",
                style={"flex": "1"},
            ),
            # Bottom: ticket — always at same level across all cards
            rx.cond(
                ev.url_billetterie,
                rx.link(
                    rx.button(
                        rx.icon("ticket", size=14),
                        "Réserver",
                        variant="surface",
                        color_scheme="violet",
                        size="1",
                        radius="full",
                    ),
                    href=ev.url_billetterie.to(str),  # type: ignore[union-attr]
                    is_external=True,
                ),
                rx.box(height="26px"),  # same height as the button, keeps alignment
            ),
            align_items="start",
            width="100%",
            style={
                "height": "100%",
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "space-between",
                "gap": "12px",
                "padding": "12px",
            },
        ),
        width="100%",
        height="100%",
        background_color="rgba(255,255,255,0.03)",
        border_radius="var(--radius-3)",
        style={"display": "flex", "flexDirection": "column"},
    )


def movie_card(m: Movie):
    return rx.box(
        rx.vstack(
            rx.vstack(
                rx.cond(
                    m.genres,
                    rx.hstack(
                        rx.foreach(
                            m.genres.split(", "),  # type: ignore[union-attr]
                            lambda g: rx.badge(
                                g, variant="soft", color_scheme="amber", radius="full"
                            ),
                        ),
                        wrap="wrap",
                        spacing="1",
                    ),
                    rx.box(),
                ),
                rx.text(m.title, size="3", weight="bold", color="white"),
                rx.cond(
                    m.producer,
                    rx.hstack(
                        rx.icon("film", size=13, color="gray"),
                        rx.text(m.producer, size="2", color="gray"),
                        spacing="1",
                        align_items="center",
                    ),
                    rx.box(),
                ),
                rx.cond(
                    m.duration,
                    rx.text(m.duration, size="2", color="gray"),
                    rx.box(),
                ),
                rx.cond(
                    m.synopsis,
                    rx.text(
                        m.synopsis,
                        size="1",
                        color="rgba(255,255,255,0.45)",
                        no_of_lines=3,
                    ),
                    rx.box(),
                ),
                spacing="2",
                align_items="start",
                width="100%",
                style={"flex": "1"},
            ),
            rx.link(
                rx.button(
                    rx.icon("info", size=14),
                    "AlloCiné",
                    variant="surface",
                    color_scheme="amber",
                    size="1",
                    radius="full",
                ),
                href="https://www.allocine.fr/rechercher/?q=" + m.title,
                is_external=True,
            ),
            align_items="start",
            width="100%",
            style={
                "height": "100%",
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "space-between",
                "gap": "12px",
                "padding": "12px",
            },
        ),
        width="100%",
        height="100%",
        background_color="rgba(255,255,255,0.03)",
        border_radius="var(--radius-3)",
        style={"display": "flex", "flexDirection": "column"},
    )


HEADER_HEIGHT = "60px"
TAB_HEIGHT = "44px"
STICKY_TOP = f"calc({HEADER_HEIGHT} + {TAB_HEIGHT})"


def about_page() -> rx.Component:
    return rx.box(
        sticky_header(),
        rx.container(
            rx.vstack(
                rx.vstack(
                    rx.heading("SynkOS", size="8", weight="bold", color="white"),
                    rx.text(
                        "Agrégateur de culture & loisirs",
                        size="4",
                        color="gray",
                    ),
                    spacing="2",
                    align_items="start",
                ),
                rx.divider(color_scheme="violet"),
                rx.vstack(
                    rx.heading("Le projet", size="5", weight="bold", color="white"),
                    rx.text(
                        "SynkOS est un projet hobby / "
                        "side-project personnel. "
                        "L'idée : agréger automatiquement "
                        "les sorties culturelles qui "
                        "m'intéressent (concerts, films, "
                        "expos…) en un seul endroit, avec "
                        "une interface applicative "
                        "disponible. L'objectif : me faire "
                        "gagner du temps et faciliter ma "
                        "veille cultuelle.",
                        size="3",
                        color="rgba(255,255,255,0.7)",
                        line_height="1.7",
                    ),
                    spacing="3",
                    align_items="start",
                    width="100%",
                ),
                rx.divider(color_scheme="violet"),
                rx.vstack(
                    rx.heading("Sources", size="5", weight="bold", color="white"),
                    rx.vstack(
                        rx.hstack(
                            rx.text("🎵", size="3"),
                            rx.text(
                                "BDXC — agenda concerts Bordeaux",
                                size="3",
                                color="rgba(255,255,255,0.7)",
                            ),
                            spacing="2",
                        ),
                        rx.hstack(
                            rx.text("🎬", size="3"),
                            rx.text(
                                "Écran Total — sorties cinéma France",
                                size="3",
                                color="rgba(255,255,255,0.7)",
                            ),
                            spacing="2",
                        ),
                        spacing="2",
                        align_items="start",
                    ),
                    spacing="3",
                    align_items="start",
                    width="100%",
                ),
                rx.divider(color_scheme="violet"),
                rx.vstack(
                    rx.heading("Liens", size="5", weight="bold", color="white"),
                    rx.hstack(
                        rx.link(
                            rx.button(
                                rx.icon("github", size=16),
                                "GitHub",
                                variant="surface",
                                color_scheme="violet",
                                radius="full",
                            ),
                            href="https://github.com/lorenzodelmedico",
                            is_external=True,
                        ),
                        rx.link(
                            rx.button(
                                rx.icon("briefcase", size=16),
                                "Malt",
                                variant="surface",
                                color_scheme="amber",
                                radius="full",
                            ),
                            href="https://www.malt.fr/profile/lorenzodelmedico",
                            is_external=True,
                        ),
                        spacing="3",
                    ),
                    spacing="3",
                    align_items="start",
                    width="100%",
                ),
                spacing="6",
                align_items="start",
                width="100%",
                padding_top="2em",
            ),
            max_width="700px",
            padding_x={"initial": "1em", "md": "2em"},
            padding_bottom="5em",
        ),
        background_color="#0a0a0a",
        min_height="100vh",
    )


def sticky_header():
    return rx.vstack(
        # Row 1: title + search + filters
        rx.hstack(
            rx.heading("SynkOS", size="6", weight="bold", color="white"),
            rx.spacer(),
            rx.input(
                placeholder="Chercher un événement...",
                value=State.search_query,
                on_change=State.set_search,
                variant="soft",
                radius="full",
                color_scheme="violet",
                width="250px",
            ),
            rx.link(
                rx.icon("info", size=18, color="gray"),
                href="/about",
                _hover={"opacity": "0.7"},
            ),
            rx.cond(
                State.active_tab == "concerts",
                rx.hstack(
                    rx.select(
                        State.unique_families,
                        value=State.selected_family,
                        on_change=State.set_family,
                        variant="soft",
                        radius="full",
                        color_scheme="violet",
                        placeholder="Genre",
                    ),
                    rx.select(
                        State.unique_cities,
                        value=State.selected_city,
                        on_change=State.set_city,
                        variant="soft",
                        radius="full",
                        color_scheme="violet",
                        placeholder="Ville",
                    ),
                    spacing="2",
                ),
                rx.hstack(
                    rx.select(
                        State.unique_genres,
                        value=State.selected_genre,
                        on_change=State.set_genre,
                        variant="soft",
                        radius="full",
                        color_scheme="amber",
                        placeholder="Genre",
                    ),
                    spacing="2",
                ),
            ),
            width="100%",
            padding_x="1em",
            padding_top="0.75em",
            padding_bottom="0",
            align_items="center",
            height=HEADER_HEIGHT,
        ),
        # Row 2: tabs
        rx.hstack(
            rx.button(
                "🎵 Concerts",
                on_click=State.go_concerts,
                variant=rx.cond(State.active_tab == "concerts", "solid", "ghost"),
                color_scheme="violet",
                radius="full",
                size="2",
            ),
            rx.button(
                "🎬 Films",
                on_click=State.go_films,
                variant=rx.cond(State.active_tab == "films", "solid", "ghost"),
                color_scheme="amber",
                radius="full",
                size="2",
            ),
            width="100%",
            padding_x="1em",
            padding_bottom="0.5em",
            spacing="2",
            height=TAB_HEIGHT,
        ),
        width="100%",
        spacing="0",
        position="sticky",
        top="0",
        z_index="50",
        background="rgba(0, 0, 0, 0.8)",
        backdrop_filter="blur(12px)",
        border_bottom="1px solid rgba(255,255,255,0.1)",
    )


def day_section(date_display, items, card_fn):
    return rx.vstack(
        rx.box(
            rx.text(date_display, size="3", weight="bold", color="gray"),
            position="sticky",
            top=STICKY_TOP,
            z_index="40",
            background="rgba(10, 10, 10, 0.9)",
            backdrop_filter="blur(8px)",
            padding_top="1.5em",
            padding_bottom="0.5em",
            width="100%",
        ),
        rx.box(
            rx.grid(
                rx.foreach(items, card_fn),
                columns={"initial": "1", "sm": "2", "lg": "3"},
                width="100%",
                gap="3",
                align_items="stretch",
            ),
            padding_left={"initial": "1em", "md": "0"},
            margin_left={"initial": "0.5em", "md": "0"},
            border_left={"initial": "1px solid rgba(255,255,255,0.1)", "md": "none"},
            width="100%",
        ),
        width="100%",
        align_items="start",
        margin_bottom="1.5em",
    )


def concerts_view():
    return rx.foreach(
        State.grouped_events_list,
        lambda day: day_section(day.date_display, day.events, event_card),
    )


def films_view():
    return rx.foreach(
        State.grouped_movies_list,
        lambda day: day_section(day.date_display, day.movies, movie_card),
    )


def search_results_view():
    """Display search results ranked by match quality."""
    return rx.container(
        rx.vstack(
            rx.heading(
                f"Résultats pour '{State.search_query}'",
                size="5",
                weight="bold",
                color="white",
            ),
            rx.foreach(
                State.search_results,
                lambda result: rx.cond(
                    result.type == "event",
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.badge(
                                    "🎵 Concert",
                                    variant="soft",
                                    color_scheme="violet",
                                    radius="full",
                                ),
                                rx.text(
                                    result.title, size="3", weight="bold", color="white"
                                ),
                                spacing="2",
                            ),
                            rx.text(
                                result.event.event_date.to(str),
                                size="2",
                                color="gray",
                            ),
                            spacing="2",
                        ),
                        padding="1em",
                        background_color="rgba(255,255,255,0.03)",
                        border_radius="var(--radius-3)",
                        margin_bottom="1em",
                        width="100%",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.badge(
                                    "🎬 Film",
                                    variant="soft",
                                    color_scheme="amber",
                                    radius="full",
                                ),
                                rx.text(
                                    result.title, size="3", weight="bold", color="white"
                                ),
                                spacing="2",
                            ),
                            rx.cond(
                                result.movie.release_date,
                                rx.text(
                                    result.movie.release_date.to(str),
                                    size="2",
                                    color="gray",
                                ),
                                rx.text("Date inconnue", size="2", color="gray"),
                            ),
                            spacing="2",
                        ),
                        padding="1em",
                        background_color="rgba(255,255,255,0.03)",
                        border_radius="var(--radius-3)",
                        margin_bottom="1em",
                        width="100%",
                    ),
                ),
            ),
            width="100%",
            spacing="2",
        ),
        max_width="1200px",
        padding_x={"initial": "1em", "md": "2em"},
        padding_bottom="5em",
        padding_top="1em",
    )


def index() -> rx.Component:
    return rx.box(
        sticky_header(),
        rx.container(
            rx.cond(
                State.search_query != "",
                search_results_view(),
                rx.vstack(
                    rx.cond(
                        State.active_tab == "concerts", concerts_view(), films_view()
                    ),
                    width="100%",
                ),
            ),
            max_width="1200px",
            padding_x={"initial": "1em", "md": "2em"},
            padding_bottom="5em",
            padding_top="1em",
        ),
        on_mount=State.load_events,
        background_color="#0a0a0a",
        min_height="100vh",
    )


app = rx.App(
    theme=rx.theme(appearance="dark", accent_color="violet", radius="full"),
    head_components=[
        # Page title
        rx.el.title("SynkOS"),
        # PWA manifest
        rx.el.link(rel="manifest", href="/manifest.json"),
        # Theme
        rx.el.meta(name="theme-color", content="#000000"),
        # iOS support
        rx.el.meta(name="apple-mobile-web-app-capable", content="yes"),
        rx.el.meta(
            name="apple-mobile-web-app-status-bar-style", content="black-translucent"
        ),
        rx.el.meta(name="apple-mobile-web-app-title", content="SynkOS"),
        # Viewport
        rx.el.meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        # Icons
        rx.el.link(rel="apple-touch-icon", href="/icon-192.png"),
        # Skip ngrok browser warning on first visit by patching fetch + XHR
        rx.el.script("""
                (function() {
                    var _fetch = window.fetch;
                    window.fetch = function(input, init) {
                        init = init || {};
                        init.headers = Object.assign(
                            {}, init.headers,
                            {'ngrok-skip-browser-warning': '1'}
                        );
                        return _fetch(input, init);
                    };
                    var _open = XMLHttpRequest.prototype.open;
                    XMLHttpRequest.prototype.open = function() {
                        _open.apply(this, arguments);
                        this.setRequestHeader('ngrok-skip-browser-warning', '1');
                    };
                })();
            """),
        # Register service worker
        rx.el.script("""
                if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/sw.js');
                }
            """),
    ],
)
app.add_page(index, title="SynkOS")
app.add_page(about_page, route="/about", title="SynkOS | About")
