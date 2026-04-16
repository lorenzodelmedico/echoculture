-- Migration 005 — BDXC rebranded to junklive.fr
-- Replace stored bdxc.fr event page URLs with the new domain.
-- The path structure is identical; slugs resolve correctly on junklive.fr.
UPDATE events
SET source_url = REPLACE(source_url, 'www.bdxc.fr', 'www.junklive.fr')
WHERE source_url LIKE '%bdxc.fr%';
