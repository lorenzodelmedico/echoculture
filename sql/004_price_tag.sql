-- Migration 004 — add price_tag column to events
-- Values: 'payant' = known paid but no specific amount; NULL = everything else
ALTER TABLE events ADD COLUMN IF NOT EXISTS price_tag TEXT;
