import reflex as rx
from .state import State
from .models import Event, Movie, TodayItem


def event_card(ev: Event):
    return rx.box(
        # Card shell — full height flex column so button is always at bottom
        rx.vstack(
            # Top section: grows to fill available space
            rx.vstack(
                rx.hstack(
                    rx.badge(
                        ev.event_type,
                        variant="soft",
                        color_scheme="violet",
                        radius="full",
                    ),
                    rx.cond(
                        ev.min_price == 0.0,
                        rx.badge(
                            ev.free_label,  # type: ignore[arg-type]
                            color_scheme="green",
                            variant="soft",
                            radius="full",
                        ),
                        rx.cond(
                            ev.min_price,
                            rx.badge(
                                ev.min_price.to(int).to(str) + "€+",  # type: ignore[union-attr]  # noqa: E501
                                color_scheme="blue",
                                variant="soft",
                                radius="full",
                            ),
                            rx.cond(
                                ev.price_tag == "payant",
                                rx.badge(
                                    rx.icon("euro", size=11),
                                    "Payant",
                                    color_scheme="orange",
                                    variant="soft",
                                    radius="full",
                                ),
                                rx.box(),
                            ),
                        ),
                    ),
                    spacing="1",
                    wrap="wrap",
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
            # Bottom: ticket + BDXC link — always at same level across all cards
            rx.hstack(
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
                    rx.box(height="26px"),
                ),
                rx.cond(
                    ev.source_url,
                    rx.link(
                        rx.button(
                            rx.icon("external-link", size=14),
                            "En savoir plus",
                            variant="surface",
                            color_scheme="gray",
                            size="1",
                            radius="full",
                        ),
                        href=ev.source_url.to(str),  # type: ignore[union-attr]
                        is_external=True,
                    ),
                    rx.box(),
                ),
                spacing="2",
                align_items="center",
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


def today_card(item: TodayItem):
    return rx.box(
        rx.vstack(
            rx.vstack(
                rx.hstack(
                    rx.cond(
                        item.item_type == "movie",
                        rx.badge(
                            "Film", variant="soft", color_scheme="amber", radius="full"
                        ),
                        rx.cond(
                            item.category == "spectacles",
                            rx.badge(
                                "Spectacle",
                                variant="soft",
                                color_scheme="pink",
                                radius="full",
                            ),
                            rx.cond(
                                item.category == "expositions",
                                rx.badge(
                                    "Expo",
                                    variant="soft",
                                    color_scheme="cyan",
                                    radius="full",
                                ),
                                rx.badge(
                                    "Concert",
                                    variant="soft",
                                    color_scheme="violet",
                                    radius="full",
                                ),
                            ),
                        ),
                    ),
                    rx.cond(
                        item.item_type == "event",
                        rx.cond(
                            item.min_price == 0.0,
                            rx.badge(
                                item.free_label,  # type: ignore
                                color_scheme="green",
                                variant="soft",
                                radius="full",
                            ),
                            rx.cond(
                                item.min_price,
                                rx.badge(
                                    item.min_price.to(int).to(str)  # type: ignore
                                    + "€+",
                                    color_scheme="blue",
                                    variant="soft",
                                    radius="full",
                                ),
                                rx.cond(
                                    item.price_tag == "payant",
                                    rx.badge(
                                        rx.icon("euro", size=11),
                                        "Payant",
                                        color_scheme="orange",
                                        variant="soft",
                                        radius="full",
                                    ),
                                    rx.box(),
                                ),
                            ),
                        ),
                        rx.box(),
                    ),
                    spacing="1",
                    wrap="wrap",
                ),
                rx.text(item.title, size="3", weight="bold", color="white"),
                rx.cond(
                    item.item_type == "event",
                    rx.cond(
                        item.location,
                        rx.hstack(
                            rx.icon("map-pin", size=13, color="gray"),
                            rx.text(item.location, size="2", color="gray"),
                            spacing="1",
                            align_items="center",
                        ),
                        rx.box(),
                    ),
                    rx.cond(
                        item.director,
                        rx.hstack(
                            rx.icon("film", size=13, color="gray"),
                            rx.text(item.director, size="2", color="gray"),
                            spacing="1",
                            align_items="center",
                        ),
                        rx.box(),
                    ),
                ),
                spacing="2",
                align_items="start",
                width="100%",
                style={"flex": "1"},
            ),
            rx.hstack(
                rx.cond(
                    item.item_type == "event",
                    rx.cond(
                        item.url_billetterie,
                        rx.link(
                            rx.button(
                                rx.icon("ticket", size=14),
                                "Réserver",
                                variant="surface",
                                color_scheme="violet",
                                size="1",
                                radius="full",
                            ),
                            href=item.url_billetterie.to(str),  # type: ignore
                            is_external=True,
                        ),
                        rx.box(height="26px"),
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
                        href="https://www.allocine.fr/rechercher/?q=" + item.title,
                        is_external=True,
                    ),
                ),
                rx.cond(
                    item.source_url,
                    rx.link(
                        rx.button(
                            rx.icon("external-link", size=14),
                            "En savoir plus",
                            variant="surface",
                            color_scheme="gray",
                            size="1",
                            radius="full",
                        ),
                        href=item.source_url.to(str),  # type: ignore
                        is_external=True,
                    ),
                    rx.box(),
                ),
                spacing="2",
                align_items="center",
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


def today_view():
    return rx.cond(
        State.today_items,
        rx.box(
            rx.grid(
                rx.foreach(State.today_items, today_card),
                columns={"initial": "1", "sm": "2", "lg": "3"},
                width="100%",
                gap="3",
                align_items="stretch",
            ),
            width="100%",
        ),
        rx.vstack(
            rx.icon("calendar-x", size=48, color="gray"),
            rx.text("Rien de prévu aujourd'hui.", size="3", color="gray"),
            align_items="center",
            padding_top="4em",
            width="100%",
        ),
    )


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
                    rx.heading(
                        "Sources principales", size="5", weight="bold", color="white"
                    ),
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
                State.active_tab == "films",
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
                    rx.cond(
                        State.has_price_data,
                        rx.select(
                            [
                                "Tous",
                                "Gratuit",
                                "Payant",
                                "< 10\u20ac",
                                "10-20\u20ac",
                                "20\u20ac+",
                                "Inconnu",
                            ],
                            value=State.selected_price_range,
                            on_change=State.set_price_range,
                            variant="soft",
                            radius="full",
                            color_scheme="green",
                            placeholder="Prix",
                        ),
                        rx.box(),
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
                "Aujourd'hui",
                on_click=State.go_today,
                variant=rx.cond(State.active_tab == "today", "solid", "ghost"),
                color_scheme="gold",
                radius="full",
                size="2",
            ),
            rx.button(
                "Concerts",
                on_click=State.go_concerts,
                variant=rx.cond(State.active_tab == "concerts", "solid", "ghost"),
                color_scheme="violet",
                radius="full",
                size="2",
            ),
            rx.button(
                "Spectacles",
                on_click=State.go_spectacles,
                variant=rx.cond(State.active_tab == "spectacles", "solid", "ghost"),
                color_scheme="pink",
                radius="full",
                size="2",
            ),
            rx.button(
                "Expos",
                on_click=State.go_expositions,
                variant=rx.cond(State.active_tab == "expositions", "solid", "ghost"),
                color_scheme="cyan",
                radius="full",
                size="2",
            ),
            rx.button(
                "Films",
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


def spectacles_view():
    return rx.foreach(
        State.grouped_spectacles_list,
        lambda day: day_section(day.date_display, day.events, event_card),
    )


def expositions_view():
    return rx.foreach(
        State.grouped_expositions_list,
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
                    result.type == "movie",
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.badge(
                                    "Film",
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
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.cond(
                                    result.type == "spectacles",
                                    rx.badge(
                                        "Spectacle",
                                        variant="soft",
                                        color_scheme="pink",
                                        radius="full",
                                    ),
                                    rx.cond(
                                        result.type == "expositions",
                                        rx.badge(
                                            "Expo",
                                            variant="soft",
                                            color_scheme="cyan",
                                            radius="full",
                                        ),
                                        rx.badge(
                                            "Concert",
                                            variant="soft",
                                            color_scheme="violet",
                                            radius="full",
                                        ),
                                    ),
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
                        State.active_tab == "today",
                        today_view(),
                        rx.cond(
                            State.active_tab == "concerts",
                            concerts_view(),
                            rx.cond(
                                State.active_tab == "spectacles",
                                spectacles_view(),
                                rx.cond(
                                    State.active_tab == "expositions",
                                    expositions_view(),
                                    films_view(),
                                ),
                            ),
                        ),
                    ),
                    # Sentinel — IntersectionObserver watches this to trigger load_more
                    rx.box(id="events-end-sentinel", height="1px", width="100%"),
                    # Loading indicator
                    rx.cond(
                        State.events_loading,
                        rx.hstack(
                            rx.spinner(size="2"),
                            rx.text("Chargement...", size="2", color="gray"),
                            spacing="2",
                            justify="center",
                            width="100%",
                            padding_y="1em",
                        ),
                        rx.box(),
                    ),
                    width="100%",
                ),
            ),
            max_width="1200px",
            padding_x={"initial": "1em", "md": "2em"},
            padding_bottom="5em",
            padding_top="1em",
        ),
        # Hidden button clicked by IntersectionObserver to trigger server-side load_more
        rx.el.button(
            id="load-more-btn",
            on_click=State.load_more_events,
            style={"display": "none"},
        ),
        # IntersectionObserver: fires when sentinel enters viewport
        # clicks hidden button to trigger load_more
        rx.el.script("""
            (function() {
                function initObserver() {
                    var sentinel = document.getElementById('events-end-sentinel');
                    var btn = document.getElementById('load-more-btn');
                    if (!sentinel || !btn) return;
                    var observer = new IntersectionObserver(function(entries) {
                        if (entries[0].isIntersecting) {
                            btn.click();
                        }
                    }, { rootMargin: '200px' });
                    observer.observe(sentinel);
                }
                // Wait for DOM, then re-init on Reflex navigation
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', initObserver);
                } else {
                    initObserver();
                }
            })();
        """),
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
        rx.el.link(rel="apple-touch-icon", href="/icon-event-192.png"),
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
