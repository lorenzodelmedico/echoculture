-- init.sql
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    signature VARCHAR(255) UNIQUE NOT NULL,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    event_type TEXT,
    event_date DATE,
    event_date_raw TEXT,
    location TEXT,
    city_computed VARCHAR(100),
    url_billetterie TEXT,
    raw_id TEXT,
    genre_family TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS movies (
    id SERIAL PRIMARY KEY,
    signature VARCHAR(255) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    director TEXT,
    producer TEXT,
    genres TEXT,
    synopsis TEXT,
    release_date DATE,
    duration TEXT,
    url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
