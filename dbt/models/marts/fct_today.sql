SELECT
    'event'       AS item_type,
    title,
    event_date    AS display_date,
    category,
    event_type,
    genre_family,
    location,
    city_computed,
    source_url,
    url_billetterie,
    min_price,
    max_price,
    free_label,
    price_tag,
    NULL::TEXT    AS genres,
    NULL::TEXT    AS director,
    NULL::TEXT    AS synopsis,
    NULL::TEXT    AS duration,
    NULL::TEXT    AS movie_url
FROM {{ ref('int_events') }}
WHERE event_date = CURRENT_DATE

UNION ALL

SELECT
    'movie'       AS item_type,
    title,
    release_date  AS display_date,
    'films'       AS category,
    NULL::TEXT    AS event_type,
    NULL::TEXT    AS genre_family,
    NULL::TEXT    AS location,
    NULL::TEXT    AS city_computed,
    NULL::TEXT    AS source_url,
    NULL::TEXT    AS url_billetterie,
    NULL::FLOAT   AS min_price,
    NULL::FLOAT   AS max_price,
    NULL::TEXT    AS free_label,
    NULL::TEXT    AS price_tag,
    genres,
    director,
    synopsis,
    duration,
    url           AS movie_url
FROM {{ ref('stg_movies') }}
WHERE release_date = CURRENT_DATE

ORDER BY item_type, title
