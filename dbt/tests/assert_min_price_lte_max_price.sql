-- Singular test: returns rows where min_price > max_price (should be zero rows)
SELECT *
FROM {{ ref('stg_events') }}
WHERE min_price IS NOT NULL
  AND max_price IS NOT NULL
  AND min_price > max_price
