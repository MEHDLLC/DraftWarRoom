-- Weekly (single-game) projection, separate from season-long projected_points.
ALTER TABLE player ADD COLUMN weekly_projection REAL DEFAULT 0;

-- Normalize defense position naming: espn_api reports "D/ST" but the app's
-- canonical code is "DST" (used by slot configs, scoring, and waiver filters).
UPDATE player SET position = 'DST' WHERE position = 'D/ST';
