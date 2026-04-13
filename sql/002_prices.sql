ALTER TABLE events
    ADD COLUMN IF NOT EXISTS source_url TEXT,
    ADD COLUMN IF NOT EXISTS min_price  FLOAT,
    ADD COLUMN IF NOT EXISTS max_price  FLOAT;

CREATE TABLE IF NOT EXISTS event_prices (
    id               SERIAL PRIMARY KEY,
    event_signature  VARCHAR(255) NOT NULL REFERENCES events(signature) ON DELETE CASCADE,
    label            TEXT NOT NULL,
    amount           FLOAT NOT NULL,
    scraped_at       TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (event_signature, label)
);
