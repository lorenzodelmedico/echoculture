-- =============================================================================
-- Migration 003 — Clean movie genres + reset prices for free_label back-fill
-- Run via Adminer or psql once, then re-trigger dag_bdxc_prices in Airflow.
-- =============================================================================

-- -----------------------------------------------------------------------
-- 1. Fix movie genres
--    - Removes dirty values ("ballads", "tragedyrefcite web", "braquage", …)
--    - Normalises casing ("Science Fiction" → "Science fiction", etc.)
--    - Keeps only values in the known genre set
-- -----------------------------------------------------------------------
WITH valid_genres (genre) AS (
    VALUES
        ('Action'), ('Adventure'), ('Animation'), ('Biography'),
        ('Comedy'), ('Crime'), ('Documentary'), ('Drama'),
        ('Fantasy'), ('History'), ('Horror'), ('Musical'),
        ('Mystery'), ('Romance'), ('Science fiction'),
        ('Sport'), ('Superhero'), ('Thriller'), ('War'), ('Western')
),
cleaned AS (
    SELECT
        m.id,
        NULLIF(
            (
                SELECT STRING_AGG(v.genre, ', ' ORDER BY v.genre)
                FROM UNNEST(STRING_TO_ARRAY(m.genres, ',')) AS raw_g
                JOIN valid_genres v
                  ON LOWER(TRIM(raw_g)) = LOWER(v.genre)
            ),
            ''
        ) AS clean_genres
    FROM movies m
    WHERE m.genres IS NOT NULL
)
UPDATE movies m
SET genres = c.clean_genres
FROM cleaned c
WHERE m.id = c.id
  AND (m.genres IS DISTINCT FROM c.clean_genres);

-- -----------------------------------------------------------------------
-- 2. Reset event prices so dag_bdxc_prices re-scrapes everything
--    This is needed to back-fill the free_label column and pick up any
--    "Prix libre" entries that the old pipeline missed.
--    After running this, trigger dag_bdxc_prices in Airflow.
-- -----------------------------------------------------------------------
DELETE FROM event_prices;

UPDATE events
SET min_price  = NULL,
    max_price  = NULL,
    free_label = NULL
WHERE min_price IS NOT NULL
   OR free_label IS NOT NULL;
