WITH base AS (
    SELECT * FROM {{ ref('stg_events') }}
),
genre_map AS (
    SELECT event_type, genre_family FROM {{ ref('genre_family_map') }}
)
SELECT
    b.id,
    b.signature,
    b.source,
    b.title,
    b.event_type,
    b.event_date,
    b.location,
    b.city_computed,
    b.url_billetterie,
    b.raw_id,
    b.source_url,
    b.min_price,
    b.max_price,
    b.free_label,
    b.price_tag,
    b.category,
    b.created_at,
    COALESCE(gm.genre_family, b.genre_family) AS genre_family,
    CASE
        WHEN b.min_price = 0   THEN 'Gratuit'
        WHEN b.min_price < 10  THEN '< 10€'
        WHEN b.min_price <= 20 THEN '10-20€'
        WHEN b.min_price > 20  THEN '20€+'
        ELSE NULL
    END AS price_bucket
FROM base b
LEFT JOIN genre_map gm ON LOWER(b.event_type) = LOWER(gm.event_type)
