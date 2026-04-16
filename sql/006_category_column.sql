-- Migration 006 — Add category column to events table
-- Supports spectacles and expositions alongside concerts.
ALTER TABLE events ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'concerts';
