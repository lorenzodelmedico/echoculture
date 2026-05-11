import reflex as rx
from .state import State
from .models import Event, Movie, TodayItem

BG_BASE = "#0A0A0B"
BG_SURFACE = "#101012"
BORDER_HAIRLINE = "#1F1F23"
BORDER_STRONG = "#2A2A2F"
FG_PRIMARY = "#F5F5F4"
FG_SECONDARY = "#A1A1A6"
FG_TERTIARY = "#6B6B70"

DATE_STICKY_TOP = {"initial": "96px", "md": "44px"}


def _tag(text):
    return rx.el.span(text, class_name="synkos-tag")


def _venue_link(location, city_computed):
    """Venue line — clickable, opens Google Maps."""
    return rx.cond(
        location,
        rx.link(
            rx.el.span(location, class_name="synkos-card-venue"),
            href="https://www.google.com/maps/search/"  # type: ignore
            + location
            + "+"
            + rx.cond(city_computed, city_computed, "Bordeaux"),  # type: ignore
            is_external=True,
            _hover={"opacity": "0.7"},
        ),
        rx.el.span("Lieu inconnu", class_name="synkos-card-venue"),
    )


def _price_node(min_price, free_label, price_tag):
    """Right-side price element on event cards."""
    return rx.cond(
        min_price == 0.0,
        rx.el.span(
            rx.cond(free_label, free_label, "ENTRÉE LIBRE"),  # type: ignore
            class_name="synkos-price synkos-price--free",
        ),
        rx.cond(
            min_price,
            rx.el.span(
                min_price.to(int).to(str) + "€+",  # type: ignore
                class_name="synkos-price",
            ),
            rx.cond(
                price_tag == "payant",
                rx.el.span("PAYANT", class_name="synkos-price"),
                rx.box(),
            ),
        ),
    )


def _cta_reserve(href):
    return rx.link(
        rx.el.span(
            "Réserver",
            rx.el.span(" →", class_name="synkos-cta-arrow"),
            class_name="synkos-cta",
        ),
        href=href,
        is_external=True,
    )


def _cta_more(href, label="En savoir plus"):
    return rx.link(
        rx.el.span(label, class_name="synkos-cta synkos-cta--muted"),
        href=href,
        is_external=True,
    )


# ============================================================
# SKILLS POPUP
# ============================================================
_SKILLS = [
    (
        "Python",
        "code",
        "blue",
        "Langage",
        "Le langage de tout le projet — du scraping des sources jusqu'à l'interface web que tu vois.",  # noqa: E501
    ),
    (
        "Apache Spark",
        "zap",
        "orange",
        "Compute",
        "Croise les artistes scrapés avec Wikipedia pour récupérer automatiquement leur genre musical.",  # noqa: E501
    ),
    (
        "Airflow",
        "wind",
        "teal",
        "Orchestration",
        "Lance chaque nuit les scrapers et la mise à jour des données, sans intervention manuelle.",  # noqa: E501
    ),
    (
        "dbt",
        "git-merge",
        "iris",
        "Transformation",
        "Transforme les données brutes en tables propres prêtes à être affichées par l'app.",  # noqa: E501
    ),
    (
        "Docker",
        "box",
        "cyan",
        "Infrastructure",
        "Empaquette tous les services (app, base, scrapers) pour les faire tourner ensemble en une commande.",  # noqa: E501
    ),
    (
        "PostgreSQL",
        "database",
        "indigo",
        "Base de données",
        "Stocke les données finales que l'app affiche : concerts, expos, films.",
    ),
    (
        "MongoDB",
        "hard-drive",
        "green",
        "Base de données",
        "Garde la trace de ce qui a déjà été scrapé pour éviter de refaire le travail chaque nuit.",  # noqa: E501
    ),
    (
        "Reflex",
        "layers",
        "violet",
        "Framework",
        "Le framework Python qui génère l'interface web — toute l'app est écrite en Python, zéro JS à la main.",  # noqa: E501
    ),
    (
        "Ollama",
        "brain",
        "plum",
        "IA / LLM",
        "Fait tourner un modèle de langage en local pour catégoriser certains événements automatiquement.",  # noqa: E501
    ),
]


def _skill_row(name, icon_name, color, category, description):
    is_open = State.expanded_skill == name
    return rx.hstack(
        rx.badge(
            rx.icon(icon_name, size=13),
            color_scheme=color,
            radius="none",
            variant="soft",
            style={"padding": "6px 8px"},
        ),
        rx.vstack(
            rx.el.span(
                name,
                style={"fontSize": "14px", "fontWeight": "500", "color": FG_PRIMARY},
            ),
            rx.cond(
                is_open,
                rx.el.span(
                    description,
                    style={
                        "fontSize": "12px",
                        "color": FG_SECONDARY,
                        "lineHeight": "1.5",
                        "transition": "opacity 0.15s ease",
                    },
                ),
                rx.el.span(
                    category, class_name="synkos-mono", style={"color": FG_TERTIARY}
                ),
            ),
            spacing="1",
            align_items="start",
            flex="1",
        ),
        rx.el.button(
            rx.cond(
                is_open,
                rx.icon("x", size=12),
                rx.icon("chevron-right", size=12),
            ),
            on_click=State.toggle_skill(name),
            style={
                "background": "transparent",
                "border": f"1px solid {BORDER_HAIRLINE}",
                "color": FG_TERTIARY,
                "padding": "4px 8px",
                "cursor": "pointer",
                "transition": "color 150ms ease, border-color 150ms ease",
                "borderRadius": "0",
                "flexShrink": "0",
            },
        ),
        width="100%",
        align_items="center",
        spacing="3",
        padding_y="12px",
        border_bottom=f"1px solid {BORDER_HAIRLINE}",
    )


def skills_popup():
    return rx.cond(
        State.skills_open,
        rx.fragment(
            rx.box(
                position="fixed",
                inset="0",
                background="rgba(0,0,0,0.7)",
                z_index="200",
                on_click=State.toggle_skills,
            ),
            rx.box(
                rx.hstack(
                    rx.vstack(
                        rx.el.span(
                            "Stack technique",
                            class_name="synkos-display",
                            style={
                                "fontSize": "18px",
                                "fontWeight": "600",
                                "color": FG_PRIMARY,
                            },
                        ),
                        rx.el.span(
                            "Cliquer un badge pour voir comment chaque techno est utilisée",  # noqa: E501
                            class_name="synkos-mono",
                            style={"color": FG_TERTIARY},
                        ),
                        spacing="1",
                        align_items="start",
                    ),
                    rx.spacer(),
                    rx.el.button(
                        rx.icon("x", size=16),
                        on_click=State.toggle_skills,
                        style={
                            "background": "transparent",
                            "border": f"1px solid {BORDER_HAIRLINE}",
                            "color": FG_TERTIARY,
                            "padding": "4px 8px",
                            "cursor": "pointer",
                            "borderRadius": "0",
                        },
                    ),
                    width="100%",
                    align_items="start",
                    margin_bottom="1.5em",
                ),
                *[_skill_row(*s) for s in _SKILLS],
                position="fixed",
                top="50%",
                left="50%",
                transform="translate(-50%, -50%)",
                width="min(480px, 90vw)",
                max_height="80vh",
                overflow_y="auto",
                background=BG_SURFACE,
                border=f"1px solid {BORDER_STRONG}",
                padding="24px",
                z_index="201",
            ),
        ),
        rx.box(),
    )


# ============================================================
# CARDS
# ============================================================
def event_card(ev: Event):
    return rx.box(
        # top row: tag + price
        rx.hstack(
            _tag(ev.event_type),
            rx.spacer(),
            _price_node(ev.min_price, ev.free_label, ev.price_tag),
            width="100%",
            align_items="center",
        ),
        # title
        rx.el.h3(ev.title, class_name="synkos-card-title", style={"marginTop": "20px"}),
        # venue + date
        rx.box(
            _venue_link(ev.location, ev.city_computed),
            margin_top="14px",
        ),
        # actions row
        rx.hstack(
            rx.cond(
                ev.url_billetterie,
                _cta_reserve(ev.url_billetterie.to(str)),  # type: ignore
                rx.box(),
            ),
            rx.spacer(),
            rx.cond(
                ev.source_url,
                _cta_more(ev.source_url.to(str)),  # type: ignore
                rx.box(),
            ),
            width="100%",
            align_items="center",
            margin_top="20px",
        ),
        class_name="synkos-card",
        width="100%",
        height="100%",
        style={
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-between",
        },
    )


def movie_card(m: Movie):
    return rx.box(
        # top row: tag + (genres mono-text on right, optional)
        rx.hstack(
            _tag("Film"),
            rx.spacer(),
            rx.cond(
                m.genres,
                rx.el.span(m.genres, class_name="synkos-tag"),  # type: ignore
                rx.box(),
            ),
            width="100%",
            align_items="center",
        ),
        rx.el.h3(m.title, class_name="synkos-card-title", style={"marginTop": "20px"}),
        rx.cond(
            m.producer,
            rx.box(
                rx.el.span(m.producer, class_name="synkos-card-venue"),
                margin_top="14px",
            ),
            rx.box(),
        ),
        rx.cond(
            m.duration,
            rx.box(
                rx.el.span(m.duration, class_name="synkos-card-meta"),
                margin_top="6px",
            ),
            rx.box(),
        ),
        rx.cond(
            m.synopsis,
            rx.box(
                rx.text(
                    m.synopsis,
                    style={
                        "fontSize": "12px",
                        "color": FG_TERTIARY,
                        "marginTop": "12px",
                        "lineHeight": "1.5",
                    },
                    no_of_lines=3,
                ),
                width="100%",
            ),
            rx.box(),
        ),
        rx.hstack(
            _cta_more(
                "https://www.allocine.fr/rechercher/?q=" + m.title,
                label="AlloCiné →",
            ),
            width="100%",
            align_items="center",
            margin_top="20px",
        ),
        class_name="synkos-card",
        width="100%",
        height="100%",
        style={
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-between",
        },
    )


def today_card(item: TodayItem):
    # category label resolves to one mono-caps tag
    tag_label = rx.cond(
        item.item_type == "movie",
        "Film",
        rx.cond(
            item.category == "spectacles",
            "Spectacle",
            rx.cond(
                item.category == "expositions",
                "Expo",
                "Concert",
            ),
        ),
    )

    return rx.box(
        rx.hstack(
            _tag(tag_label),
            rx.spacer(),
            rx.cond(
                item.item_type == "event",
                _price_node(item.min_price, item.free_label, item.price_tag),
                rx.box(),
            ),
            width="100%",
            align_items="center",
        ),
        rx.el.h3(
            item.title, class_name="synkos-card-title", style={"marginTop": "20px"}
        ),
        rx.cond(
            item.item_type == "event",
            rx.box(
                _venue_link(item.location, item.city_computed),
                margin_top="14px",
            ),
            rx.cond(
                item.director,
                rx.box(
                    rx.el.span(item.director, class_name="synkos-card-venue"),
                    margin_top="14px",
                ),
                rx.box(),
            ),
        ),
        rx.hstack(
            rx.cond(
                item.item_type == "event",
                rx.cond(
                    item.url_billetterie,
                    _cta_reserve(item.url_billetterie.to(str)),  # type: ignore
                    rx.box(),
                ),
                _cta_more(
                    "https://www.allocine.fr/rechercher/?q=" + item.title,
                    label="AlloCiné →",
                ),
            ),
            rx.spacer(),
            rx.cond(
                item.source_url,
                _cta_more(item.source_url.to(str)),  # type: ignore
                rx.box(),
            ),
            width="100%",
            align_items="center",
            margin_top="20px",
        ),
        class_name="synkos-card",
        width="100%",
        height="100%",
        style={
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-between",
        },
    )


# ============================================================
# BOTTOM NAV (primary navigation — all viewports)
# ============================================================
def _bottom_btn(label, icon_name, on_click, is_active):
    return rx.el.button(
        rx.icon(icon_name, size=20),
        rx.el.span(label, class_name="synkos-bottom-btn-label"),
        on_click=on_click,
        class_name=rx.cond(
            is_active,
            "synkos-bottom-btn synkos-bottom-btn--active",
            "synkos-bottom-btn",
        ),
        aria_label=label,
    )


def bottom_nav():
    return rx.box(
        _bottom_btn("Today", "sparkle", State.go_today, State.active_tab == "today"),
        _bottom_btn(
            "Concerts", "disc-3", State.go_concerts, State.active_tab == "concerts"
        ),
        _bottom_btn(
            "Shows", "drama", State.go_spectacles, State.active_tab == "spectacles"
        ),
        _bottom_btn(
            "Exhibits", "frame", State.go_expositions, State.active_tab == "expositions"
        ),
        _bottom_btn(
            "Films", "clapperboard", State.go_films, State.active_tab == "films"
        ),
        _bottom_btn("About", "info", State.go_about, State.active_tab == "about"),
        class_name="synkos-bottom-nav",
    )


# ============================================================
# SKELETON LOADERS (perceived-loading placeholders)
# ============================================================
def _skel(width, height, margin_top="0"):
    return rx.box(
        class_name="synkos-skeleton-block",
        style={"width": width, "height": height, "marginTop": margin_top},
    )


def skeleton_card():
    return rx.box(
        rx.hstack(
            _skel("60px", "10px"),
            rx.spacer(),
            _skel("40px", "10px"),
            width="100%",
            align_items="center",
        ),
        _skel("75%", "16px", margin_top="22px"),
        _skel("50%", "12px", margin_top="14px"),
        _skel("35%", "10px", margin_top="22px"),
        class_name="synkos-card",
        width="100%",
        height="100%",
        style={"display": "flex", "flexDirection": "column"},
    )


def skeleton_grid(count: int = 6):
    return rx.box(
        *[skeleton_card() for _ in range(count)],
        class_name="synkos-grid",
        width="100%",
    )


# ============================================================
# TOP BAR — title (mobile) + sticky filter row
# ============================================================
def top_bar():
    return rx.box(
        # Header row: title left, search right (always visible, all viewports)
        rx.hstack(
            rx.heading(
                "SynkOS",
                class_name="synkos-display",
                style={
                    "fontSize": "22px",
                    "fontWeight": "600",
                    "color": FG_PRIMARY,
                    "letterSpacing": "-0.01em",
                },
            ),
            rx.spacer(),
            rx.input(
                placeholder="Search",
                value=State.search_query,
                on_change=State.set_search,
                variant="surface",
                color_scheme="gray",
                radius="none",
                size="2",
                max_width="240px",
                style={
                    "fontFamily": "'JetBrains Mono', monospace",
                    "fontSize": "11px",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.06em",
                    "background": "transparent",
                    "border": f"1px solid {BORDER_HAIRLINE}",
                },
            ),
            padding_x="1.25em",
            padding_top="0.85em",
            padding_bottom="0.5em",
            align_items="center",
            spacing="3",
            width="100%",
        ),
        # filter row
        rx.hstack(
            rx.cond(
                State.active_tab == "today",
                rx.cond(
                    State.has_multiple_today_types,
                    rx.select(
                        State.today_types_available,
                        value=State.selected_today_type,
                        on_change=State.set_today_type,
                        variant="surface",
                        color_scheme="gray",
                        radius="none",
                        size="1",
                    ),
                    rx.box(),
                ),
                rx.box(),
            ),
            rx.cond(
                State.active_tab == "films",
                rx.cond(
                    State.has_multiple_genres,
                    rx.select(
                        State.unique_genres,
                        value=State.selected_genre,
                        on_change=State.set_genre,
                        variant="surface",
                        color_scheme="gray",
                        radius="none",
                        size="1",
                        placeholder="Genre",
                    ),
                    rx.box(),
                ),
                rx.box(),
            ),
            rx.cond(
                (State.active_tab != "today") & (State.active_tab != "films"),
                rx.hstack(
                    rx.cond(
                        State.has_multiple_families,
                        rx.select(
                            State.unique_families,
                            value=State.selected_family,
                            on_change=State.set_family,
                            variant="surface",
                            color_scheme="gray",
                            radius="none",
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
                            variant="surface",
                            color_scheme="gray",
                            radius="none",
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
                                "< 10€",
                                "10-20€",
                                "20€+",
                                "Inconnu",
                            ],
                            value=State.selected_price_range,
                            on_change=State.set_price_range,
                            variant="surface",
                            color_scheme="gray",
                            radius="none",
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
            class_name="synkos-filter-row",
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
        background="rgba(10,10,10,0.88)",
        backdrop_filter="blur(12px)",
        border_bottom=f"1px solid {BORDER_HAIRLINE}",
        width="100%",
    )


# ============================================================
# DAY SECTION + VIEWS
# ============================================================
def day_section(date_display, items, card_fn):
    return rx.vstack(
        rx.box(
            rx.el.span(date_display, class_name="synkos-day-header"),
            position="sticky",
            top=DATE_STICKY_TOP,
            z_index="40",
            background="rgba(10,10,10,0.92)",
            backdrop_filter="blur(8px)",
            padding_top="1.75em",
            padding_bottom="0.75em",
            width="100%",
        ),
        rx.box(
            rx.foreach(items, card_fn),
            class_name="synkos-grid",
            width="100%",
        ),
        width="100%",
        align_items="start",
        margin_bottom="2em",
        spacing="2",
    )


def _today_section(label, items):
    return rx.cond(
        items,
        rx.vstack(
            rx.box(
                rx.el.span(label, class_name="synkos-day-header"),
                width="100%",
                padding_top="1.5em",
                padding_bottom="0.75em",
                border_bottom=f"1px solid {BORDER_HAIRLINE}",
            ),
            rx.box(
                rx.foreach(items, today_card),
                class_name="synkos-grid",
                width="100%",
            ),
            width="100%",
            align_items="start",
            margin_bottom="2em",
            spacing="0",
        ),
        rx.box(),
    )


def today_view():
    return rx.cond(
        State.today_loading,
        skeleton_grid(6),
        rx.cond(
            State.today_items,
            rx.vstack(
                _today_section("Concerts", State.today_concerts),
                _today_section("Spectacles", State.today_spectacles),
                _today_section("Expos", State.today_expos),
                _today_section("Films", State.today_movies),
                width="100%",
                spacing="0",
                align_items="start",
            ),
            rx.vstack(
                rx.icon("calendar-x", size=42, color=FG_TERTIARY),
                rx.el.span(
                    "Rien de prévu aujourd'hui.",
                    class_name="synkos-mono",
                    style={"color": FG_TERTIARY, "marginTop": "12px"},
                ),
                align_items="center",
                padding_top="4em",
                width="100%",
            ),
        ),
    )


def concerts_view():
    return rx.cond(
        State.concerts_loading,
        skeleton_grid(6),
        rx.foreach(
            State.grouped_events_list,
            lambda day: day_section(day.date_display, day.events, event_card),
        ),
    )


def spectacles_view():
    return rx.cond(
        State.spectacles_loading,
        skeleton_grid(6),
        rx.foreach(
            State.grouped_spectacles_list,
            lambda day: day_section(day.date_display, day.events, event_card),
        ),
    )


def expositions_view():
    return rx.cond(
        State.expositions_loading,
        skeleton_grid(6),
        rx.foreach(
            State.grouped_expositions_list,
            lambda day: day_section(day.date_display, day.events, event_card),
        ),
    )


def films_view():
    return rx.cond(
        State.films_loading,
        skeleton_grid(6),
        rx.foreach(
            State.grouped_movies_list,
            lambda day: day_section(day.date_display, day.movies, movie_card),
        ),
    )


def search_results_view():
    return rx.vstack(
        rx.el.span(
            "Résultats pour « " + State.search_query + " »",
            class_name="synkos-mono",
            style={"color": FG_TERTIARY, "paddingTop": "1em"},
        ),
        rx.cond(
            State.search_results,
            rx.box(
                rx.foreach(
                    State.search_results,
                    lambda r: rx.cond(
                        r.type == "movie",
                        movie_card(r.movie),  # type: ignore
                        event_card(r.event),  # type: ignore
                    ),
                ),
                class_name="synkos-grid",
                width="100%",
            ),
            rx.vstack(
                rx.icon("search-x", size=42, color=FG_TERTIARY),
                rx.el.span(
                    "Aucun résultat.",
                    class_name="synkos-mono",
                    style={"color": FG_TERTIARY, "marginTop": "12px"},
                ),
                align_items="center",
                padding_top="3em",
                width="100%",
            ),
        ),
        rx.box(
            rx.link(
                rx.hstack(
                    rx.icon("info", size=13, color=FG_TERTIARY),
                    rx.el.span(
                        "À propos de SynkOS",
                        class_name="synkos-mono",
                        style={"color": FG_TERTIARY},
                    ),
                    spacing="2",
                    align_items="center",
                ),
                href="/about",
                _hover={"opacity": "0.7"},
            ),
            padding_top="2em",
        ),
        width="100%",
        align_items="start",
    )


# ============================================================
# PAGES
# ============================================================
def index() -> rx.Component:
    return rx.box(
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
                            rx.spinner(size="1"),
                            rx.el.span(
                                "Loading",
                                class_name="synkos-mono",
                                style={"color": FG_TERTIARY},
                            ),
                            spacing="2",
                            justify="center",
                            width="100%",
                            padding_y="1.5em",
                        ),
                        rx.box(),
                    ),
                    width="100%",
                    spacing="0",
                ),
            ),
            width="100%",
            max_width="1200px",
            margin_x="auto",
            padding_x="1.25em",
            padding_top="0.5em",
            padding_bottom="7em",
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
                    }, { rootMargin: '1000px' });
                    observer.observe(sentinel);
                }
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', initObserver);
                } else {
                    initObserver();
                }
            })();
        """),
        background_color=BG_BASE,
        min_height="100vh",
    )


def about_page() -> rx.Component:
    return rx.box(
        skills_popup(),
        top_bar(),
        rx.box(
            rx.vstack(
                # Profile header
                rx.vstack(
                    rx.image(
                        src="/ldm-personal-photo.jpg",
                        width="200px",
                        height="200px",
                        style={
                            "objectFit": "contain",
                            "borderRadius": "50%",
                            "display": "block",
                            "background": "#18181B",
                        },
                    ),
                    rx.vstack(
                        rx.heading(
                            "Lorenzo Del Medico",
                            class_name="synkos-display",
                            style={
                                "fontSize": "28px",
                                "fontWeight": "600",
                                "color": FG_PRIMARY,
                            },
                        ),
                        rx.el.span(
                            "Data Engineer · Bordeaux",
                            class_name="synkos-mono",
                            style={"color": FG_TERTIARY},
                        ),
                        spacing="1",
                        align_items="center",
                    ),
                    spacing="4",
                    align_items="center",
                    width="100%",
                ),
                rx.box(class_name="synkos-divider"),
                # Le projet
                rx.vstack(
                    rx.el.span(
                        "Le projet",
                        class_name="synkos-mono",
                        style={"color": FG_TERTIARY},
                    ),
                    rx.text(
                        "SynkOS est un projet hobby personnel. L'idée : agréger "
                        "automatiquement les sorties culturelles qui m'intéressent "
                        "(concerts, films, expos…) en un seul endroit, avec une "
                        "interface applicative disponible. L'objectif : me faire "
                        "gagner du temps et faciliter ma veille culturelle.",
                        style={
                            "fontSize": "15px",
                            "color": FG_SECONDARY,
                            "lineHeight": "1.7",
                        },
                    ),
                    spacing="3",
                    align_items="start",
                    width="100%",
                ),
                rx.box(class_name="synkos-divider"),
                # Stack technique
                rx.vstack(
                    rx.el.span(
                        "Stack technique",
                        class_name="synkos-mono",
                        style={"color": FG_TERTIARY},
                    ),
                    rx.el.button(
                        rx.hstack(
                            rx.icon("layers", size=13),
                            rx.el.span("Voir la stack →", class_name="synkos-cta"),
                            spacing="2",
                            align_items="center",
                        ),
                        on_click=State.toggle_skills,
                        style={
                            "background": "transparent",
                            "border": f"1px solid {BORDER_HAIRLINE}",
                            "padding": "8px 14px",
                            "cursor": "pointer",
                            "transition": "border-color 150ms ease",
                            "borderRadius": "0",
                        },
                    ),
                    spacing="3",
                    align_items="start",
                    width="100%",
                ),
                rx.box(class_name="synkos-divider"),
                # Sources
                rx.vstack(
                    rx.el.span(
                        "Sources",
                        class_name="synkos-mono",
                        style={"color": FG_TERTIARY},
                    ),
                    rx.vstack(
                        rx.el.span(
                            "BDXC — agenda concerts Bordeaux",
                            style={"fontSize": "14px", "color": FG_SECONDARY},
                        ),
                        rx.el.span(
                            "Écran Total — sorties cinéma France",
                            style={"fontSize": "14px", "color": FG_SECONDARY},
                        ),
                        spacing="2",
                        align_items="start",
                    ),
                    spacing="3",
                    align_items="start",
                    width="100%",
                ),
                rx.box(class_name="synkos-divider"),
                # Liens
                rx.vstack(
                    rx.el.span(
                        "Liens",
                        class_name="synkos-mono",
                        style={"color": FG_TERTIARY},
                    ),
                    rx.hstack(
                        rx.link(
                            rx.hstack(
                                rx.icon("linkedin", size=15),
                                rx.el.span("LinkedIn", class_name="synkos-cta"),
                                spacing="2",
                                align_items="center",
                            ),
                            href="https://www.linkedin.com/in/lorenzo-del-medico/",
                            is_external=True,
                            _hover={"opacity": "0.7"},
                        ),
                        rx.link(
                            rx.hstack(
                                rx.icon("github", size=15),
                                rx.el.span("GitHub", class_name="synkos-cta"),
                                spacing="2",
                                align_items="center",
                            ),
                            href="https://github.com/lorenzodelmedico",
                            is_external=True,
                            _hover={"opacity": "0.7"},
                        ),
                        rx.link(
                            rx.hstack(
                                rx.icon("briefcase", size=15),
                                rx.el.span("Malt", class_name="synkos-cta"),
                                spacing="2",
                                align_items="center",
                            ),
                            href="https://www.malt.fr/profile/lorenzodelmedico",
                            is_external=True,
                            _hover={"opacity": "0.7"},
                        ),
                        spacing="6",
                    ),
                    spacing="3",
                    align_items="start",
                    width="100%",
                ),
                spacing="6",
                align_items="start",
                width="100%",
            ),
            max_width="640px",
            width="100%",
            margin_x="auto",
            padding_x={"initial": "1.5em", "md": "2em"},
            padding_top="2em",
            padding_bottom="7em",
        ),
        bottom_nav(),
        background_color=BG_BASE,
        min_height="100vh",
    )


# ============================================================
# APP CONFIG
# ============================================================
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="lime",  # was "violet"
        radius="none",  # was "full"
        gray_color="mauve",
    ),
    head_components=[
        rx.el.title("SynkOS"),
        rx.el.link(rel="manifest", href="/manifest.json"),
        rx.el.link(rel="stylesheet", href="/synkos.v2.css"),
        rx.el.meta(name="theme-color", content="#0A0A0B"),
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
app.add_page(
    about_page, route="/about", on_load=State.on_load_about, title="SynkOS | About"
)
