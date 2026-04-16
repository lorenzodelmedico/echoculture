SELECT *
FROM {{ ref('int_events') }}
WHERE category = 'spectacles'
  AND event_date >= CURRENT_DATE - INTERVAL '1 day'
ORDER BY event_date
