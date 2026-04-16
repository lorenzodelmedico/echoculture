SELECT
    id,
    signature,
    source,
    title,
    event_type,
    event_date,
    location,
    city_computed,
    url_billetterie,
    genre_family,
    raw_id,
    source_url,
    min_price,
    max_price,
    free_label,
    price_tag,
    category,
    created_at
FROM {{ source('echoculture', 'events') }}
WHERE title IS NOT NULL
  AND event_date IS NOT NULL
