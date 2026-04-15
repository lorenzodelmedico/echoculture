SELECT
    id,
    signature,
    title,
    director,
    producer,
    CASE
        WHEN genres IS NULL THEN NULL
        ELSE ARRAY_TO_STRING(
            ARRAY(
                SELECT DISTINCT TRIM(g)
                FROM UNNEST(STRING_TO_ARRAY(genres, ',')) AS g
                WHERE TRIM(g) != ''
                ORDER BY 1
            ),
            ', '
        )
    END AS genres,
    synopsis,
    release_date,
    duration,
    url
FROM {{ ref('stg_movies') }}
