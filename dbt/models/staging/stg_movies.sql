SELECT
    id,
    signature,
    title,
    director,
    producer,
    NULLIF(TRIM(genres), '') AS genres,
    synopsis,
    release_date,
    duration,
    url
FROM {{ source('echoculture', 'movies') }}
WHERE title IS NOT NULL
