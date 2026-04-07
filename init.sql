-- init.sql
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    event_type TEXT,
    event_date DATE,
    event_date_raw TEXT,
    location TEXT,
    raw_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE events ADD CONSTRAINT unique_event UNIQUE (title, event_date, source);
-- Index pour accélérer les recherches par source
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
