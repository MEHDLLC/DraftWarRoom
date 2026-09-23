-- Normalize roster slot labels stored from espn_api to canonical names,
-- so slot comparisons and the write API's slot-id mapping work.
UPDATE roster_entry SET slot = 'DST' WHERE slot = 'D/ST';
UPDATE roster_entry SET slot = 'FLEX' WHERE slot IN ('RB/WR/TE', 'RB/WR', 'WR/TE');
