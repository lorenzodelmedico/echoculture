SELECT *
FROM {{ ref('int_movies') }}
WHERE release_date IS NOT NULL
ORDER BY release_date
