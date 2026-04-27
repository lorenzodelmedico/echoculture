import reflex as rx
from .state import State
from .models import Event, Movie, TodayItem

SIDEBAR_WIDTH = "200px"
# Sticky date-header top offset: desktop = filter bar only, mobile = title+search+filter
DATE_STICKY_TOP = {"initial": "96px", "md": "44px"}


def event_card(ev: Event):
    return rx.box(
        rx.vstack(
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


def _nav_btn(label, on_click, is_active, icon_name, color):
    return rx.button(
        rx.icon(icon_name, size=14),
        label,
        on_click=on_click,
        variant=rx.cond(is_active, "solid", "ghost"),
        color_scheme=color,
        radius="large",
        size="2",
        style={"justifyContent": "flex-start", "width": "100%"},
    )


def sidebar():
    return rx.fragment(
        # --- THE TOGGLE BUTTON ---
        # This button stays visible so the user can open the sidebar
        rx.button(
            rx.icon(tag=rx.cond(State.sidebar_open, "chevron-left", "chevron-right")),
            on_click=State.toggle_sidebar,
            position="fixed",
            top="6em",
            # Move the button with the sidebar
            left=rx.cond(State.sidebar_open, "260px", "10px"),
            z_index="101",
            variant="soft",
            color_scheme="violet",
            transition="left 0.3s ease-in-out",  # Smooth sliding
        ),
        rx.box(
            rx.vstack(
                rx.heading("SynkOS", size="5", weight="bold", color="white"),
                rx.input(
                    placeholder="Rechercher...",
                    value=State.search_query,
                    on_change=State.set_search,
                    variant="soft",
                    radius="full",
                    color_scheme="violet",
                    width="100%",
                ),
                rx.vstack(
                    _nav_btn(
                        "Aujourd'hui",
                        State.go_today,
                        State.active_tab == "today",
                        "sun",
                        "gold",
                    ),
                    _nav_btn(
                        "Concerts",
                        State.go_concerts,
                        State.active_tab == "concerts",
                        "music",
                        "violet",
                    ),
                    _nav_btn(
                        "Spectacles",
                        State.go_spectacles,
                        State.active_tab == "spectacles",
                        "sparkles",
                        "pink",
                    ),
                    _nav_btn(
                        "Expos",
                        State.go_expositions,
                        State.active_tab == "expositions",
                        "layout-grid",
                        "cyan",
                    ),
                    _nav_btn(
                        "Films",
                        State.go_films,
                        State.active_tab == "films",
                        "film",
                        "amber",
                    ),
                    width="100%",
                    spacing="1",
                    padding_top="0.5em",
                ),
                rx.spacer(),
                rx.link(
                    rx.hstack(
                        rx.icon("info", size=13),
                        rx.text("À propos", size="2"),
                        spacing="2",
                        align_items="center",
                    ),
                    href="/about",
                    color="gray",
                    _hover={"opacity": "0.7"},
                ),
                spacing="4",
                padding="1em",
                width="100%",
                height="100%",
            ),
            position="fixed",
            top="0",
            # Logic: If closed, hide it to the left by its own width
            left=rx.cond(State.sidebar_open, "0", "-250px"),
            height="100vh",
            width="250px",  # Use a fixed string or your SIDEBAR_WIDTH variable
            background="rgba(10,10,10,0.98)",
            border_right="1px solid rgba(255,255,255,0.07)",
            z_index="100",
            display="flex",  # Removed "none" so it's always "there" but off-screen
            flex_direction="column",
            transition="left 0.3s ease-in-out",  # Smooth sliding animation
        ),
    )


def bottom_nav():
    return rx.box(
        rx.hstack(
            rx.button(
                rx.icon("sun", size=19),
                on_click=State.go_today,
                variant=rx.cond(State.active_tab == "today", "solid", "ghost"),
                color_scheme="gold",
                size="2",
                radius="full",
            ),
            rx.button(
                rx.icon("music", size=19),
                on_click=State.go_concerts,
                variant=rx.cond(State.active_tab == "concerts", "solid", "ghost"),
                color_scheme="violet",
                size="2",
                radius="full",
            ),
            rx.button(
                rx.icon("sparkles", size=19),
                on_click=State.go_spectacles,
                variant=rx.cond(State.active_tab == "spectacles", "solid", "ghost"),
                color_scheme="pink",
                size="2",
                radius="full",
            ),
            rx.button(
                rx.icon("layout-grid", size=19),
                on_click=State.go_expositions,
                variant=rx.cond(State.active_tab == "expositions", "solid", "ghost"),
                color_scheme="cyan",
                size="2",
                radius="full",
            ),
            rx.button(
                rx.icon("film", size=19),
                on_click=State.go_films,
                variant=rx.cond(State.active_tab == "films", "solid", "ghost"),
                color_scheme="amber",
                size="2",
                radius="full",
            ),
            justify="between",
            width="100%",
            padding_x="0.5em",
            align_items="center",
        ),
        position="fixed",
        bottom="0",
        left="0",
        width="100%",
        height="56px",
        background="rgba(0,0,0,0.92)",
        backdrop_filter="blur(12px)",
        border_top="1px solid rgba(255,255,255,0.1)",
        z_index="100",
        display={"initial": "flex", "md": "none"},
        align_items="center",
    )


def top_bar():
    """Sticky filter bar. Mobile: adds title+search row above filters."""
    return rx.box(
        # Mobile only: title + search
        rx.box(
            rx.hstack(
                rx.heading("SynkOS", size="5", weight="bold", color="white"),
                rx.spacer(),
                rx.input(
                    placeholder="Rechercher...",
                    value=State.search_query,
                    on_change=State.set_search,
                    variant="soft",
                    radius="full",
                    color_scheme="violet",
                    size="1",
                    max_width="160px",
                ),
                padding_x="1em",
                padding_top="0.6em",
                padding_bottom="0.25em",
                align_items="center",
                width="100%",
            ),
            display={"initial": "block", "md": "none"},
        ),
        # Filters row
        rx.hstack(
            # TODAY: type filter — only when multiple types present
            rx.cond(
                State.active_tab == "today",
                rx.cond(
                    State.has_multiple_today_types,
                    rx.select(
                        State.today_types_available,
                        value=State.selected_today_type,
                        on_change=State.set_today_type,
                        variant="soft",
                        radius="full",
                        color_scheme="gold",
                        size="1",
                    ),
                    rx.box(),
                ),
                rx.box(),
            ),
            # FILMS: genre filter
            rx.cond(
                State.active_tab == "films",
                rx.cond(
                    State.has_multiple_genres,
                    rx.select(
                        State.unique_genres,
                        value=State.selected_genre,
                        on_change=State.set_genre,
                        variant="soft",
                        radius="full",
                        color_scheme="amber",
                        size="1",
                        placeholder="Genre",
                    ),
                    rx.box(),
                ),
                rx.box(),
            ),
            # EVENTS: family + city + price
            rx.cond(
                (State.active_tab != "today") & (State.active_tab != "films"),
                rx.hstack(
                    rx.cond(
                        State.has_multiple_families,
                        rx.select(
                            State.unique_families,
                            value=State.selected_family,
                            on_change=State.set_family,
                            variant="soft",
                            radius="full",
                            color_scheme="violet",
                            size="1",
                            placeholder="Genre",
                        ),
                        rx.box(),
                    ),
                    rx.cond(
                        State.has_multiple_cities,
                        rx.select(
                            State.unique_cities,
                            value=State.selected_city,
                            on_change=State.set_city,
                            variant="soft",
                            radius="full",
                            color_scheme="violet",
                            size="1",
                            placeholder="Ville",
                        ),
                        rx.box(),
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
                            size="1",
                            placeholder="Prix",
                        ),
                        rx.box(),
                    ),
                    spacing="2",
                    wrap="wrap",
                    align_items="center",
                ),
                rx.box(),
            ),
            padding_x="1em",
            padding_y="0.5em",
            spacing="2",
            wrap="wrap",
            align_items="center",
            width="100%",
            min_height="44px",
        ),
        position="sticky",
        top="0",
        z_index="50",
        background="rgba(0,0,0,0.85)",
        backdrop_filter="blur(12px)",
        border_bottom="1px solid rgba(255,255,255,0.08)",
        width="100%",
    )


def day_section(date_display, items, card_fn):
    return rx.vstack(
        rx.box(
            rx.text(date_display, size="3", weight="bold", color="gray"),
            position="sticky",
            top=DATE_STICKY_TOP,
            z_index="40",
            background="rgba(10, 10, 10, 0.9)",
            backdrop_filter="blur(8px)",
            padding_top="1.5em",
            padding_bottom="0.5em",
            width="100%",
        ),
        rx.box(
            rx.foreach(items, card_fn),
            padding_left={"initial": "1em", "md": "0"},
            margin_left={"initial": "0.5em", "md": "0"},
            border_left={"initial": "1px solid rgba(255,255,255,0.1)", "md": "none"},
            width="100%",
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fill, minmax(300px, 1fr))",
                "gap": "12px",
                "alignItems": "stretch",
            },
        ),
        width="100%",
        align_items="start",
        margin_bottom="1.5em",
    )


def today_view():
    return rx.cond(
        State.today_items,
        rx.box(
            rx.foreach(State.filtered_today_items, today_card),
            width="100%",
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fill, minmax(300px, 1fr))",
                "gap": "12px",
                "alignItems": "stretch",
            },
        ),
        rx.vstack(
            rx.icon("calendar-x", size=48, color="gray"),
            rx.text("Rien de prévu aujourd'hui.", size="3", color="gray"),
            align_items="center",
            padding_top="4em",
            width="100%",
        ),
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
    return rx.vstack(
        rx.text(
            "Résultats pour « " + State.search_query + " »",
            size="3",
            color="gray",
            padding_top="1em",
        ),
        rx.box(
            rx.foreach(
                State.search_results,
                lambda result: rx.cond(
                    result.type == "movie",
                    movie_card(result.movie),  # type: ignore[arg-type]
                    event_card(result.event),  # type: ignore[arg-type]
                ),
            ),
            width="100%",
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fill, minmax(300px, 1fr))",
                "gap": "12px",
                "alignItems": "stretch",
            },
        ),
        width="100%",
        spacing="3",
    )


def index() -> rx.Component:
    return rx.box(
        sidebar(),
        rx.box(
            top_bar(),
            rx.box(
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
                        rx.box(id="events-end-sentinel", height="1px", width="100%"),
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
                width="100%",
                padding_x={"initial": "1em", "md": "2em"},
                padding_top="1em",
                padding_bottom="2em",
            ),
            margin_left={"initial": "0", "md": SIDEBAR_WIDTH},
            padding_bottom={"initial": "64px", "md": "0"},
        ),
        bottom_nav(),
        rx.el.button(
            id="load-more-btn",
            on_click=State.load_more_events,
            style={"display": "none"},
        ),
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
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', initObserver);
                } else {
                    initObserver();
                }
            })();
        """),
        background_color="#0a0a0a",
        min_height="100vh",
    )


def about_page() -> rx.Component:
    return rx.box(
        sidebar(),
        rx.box(
            rx.box(
                rx.hstack(
                    rx.heading("SynkOS", size="5", weight="bold", color="white"),
                    rx.spacer(),
                    rx.link(
                        rx.icon("arrow-left", size=16, color="gray"),
                        href="/",
                        _hover={"opacity": "0.7"},
                    ),
                    padding_x="1em",
                    padding_y="0.75em",
                    align_items="center",
                    width="100%",
                ),
                display={"initial": "flex", "md": "none"},
                border_bottom="1px solid rgba(255,255,255,0.08)",
            ),
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
                            "Sources principales",
                            size="5",
                            weight="bold",
                            color="white",
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
            margin_left={"initial": "0", "md": SIDEBAR_WIDTH},
            padding_bottom={"initial": "64px", "md": "0"},
        ),
        bottom_nav(),
        background_color="#0a0a0a",
        min_height="100vh",
    )


app = rx.App(
    theme=rx.theme(appearance="dark", accent_color="violet", radius="full"),
    head_components=[
        rx.el.title("SynkOS"),
        rx.el.link(rel="manifest", href="/manifest.json"),
        rx.el.meta(name="theme-color", content="#000000"),
        rx.el.meta(name="apple-mobile-web-app-capable", content="yes"),
        rx.el.meta(
            name="apple-mobile-web-app-status-bar-style", content="black-translucent"
        ),
        rx.el.meta(name="apple-mobile-web-app-title", content="SynkOS"),
        rx.el.meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        rx.el.link(rel="apple-touch-icon", href="/icon-event-192.png"),
        rx.el.script("""
                if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/sw.js');
                }
            """),
    ],
)
app.add_page(index, route="/", on_load=State.on_load_today, title="SynkOS")
app.add_page(
    index, route="/concerts", on_load=State.on_load_concerts, title="SynkOS · Concerts"
)
app.add_page(
    index,
    route="/spectacles",
    on_load=State.on_load_spectacles,
    title="SynkOS · Spectacles",
)
app.add_page(
    index,
    route="/expositions",
    on_load=State.on_load_expositions,
    title="SynkOS · Expos",
)
app.add_page(index, route="/films", on_load=State.on_load_films, title="SynkOS · Films")
app.add_page(about_page, route="/about", title="SynkOS | About")
