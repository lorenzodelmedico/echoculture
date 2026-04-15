SELECT *
FROM {{ ref('int_events') }}
WHERE event_date >= CURRENT_DATE - INTERVAL '1 day'
ORDER BY event_date
