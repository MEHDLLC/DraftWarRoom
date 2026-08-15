-- League settings
CREATE TABLE IF NOT EXISTS league (
    id INTEGER PRIMARY KEY,
    espn_id INTEGER NOT NULL UNIQUE,
    name TEXT NOT NULL,
    season INTEGER NOT NULL,
    current_week INTEGER DEFAULT 1,
    num_teams INTEGER DEFAULT 10,
    scoring_type TEXT DEFAULT 'PPR',
    playoff_start_week INTEGER DEFAULT 15,
    roster_slots TEXT, -- JSON: {"QB":1,"RB":2,"WR":2,"TE":1,"FLEX":1,"DST":1,"K":1,"BE":6,"IR":1}
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Teams in the league
CREATE TABLE IF NOT EXISTS team (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    espn_team_id INTEGER NOT NULL,
    league_id INTEGER NOT NULL REFERENCES league(id),
    owner_name TEXT,
    team_name TEXT NOT NULL,
    abbreviation TEXT,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    ties INTEGER DEFAULT 0,
    points_for REAL DEFAULT 0,
    points_against REAL DEFAULT 0,
    streak TEXT,
    waiver_rank INTEGER,
    is_user_team INTEGER DEFAULT 0,
    power_rank_score REAL,
    playoff_probability REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(espn_team_id, league_id)
);

-- Player master table
CREATE TABLE IF NOT EXISTS player (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    espn_id INTEGER UNIQUE,
    sleeper_id TEXT,
    full_name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    position TEXT NOT NULL, -- QB, RB, WR, TE, K, DST
    nfl_team TEXT,
    jersey_number INTEGER,
    status TEXT, -- ACTIVE, INJURED_RESERVE, OUT, DOUBTFUL, QUESTIONABLE, PROBABLE
    injury_status TEXT,
    injury_body_part TEXT,
    -- Projections & scores
    projected_points REAL DEFAULT 0,
    ros_projection REAL DEFAULT 0,
    composite_score REAL DEFAULT 0,
    trade_value REAL DEFAULT 0,
    -- Boom/bust
    boom_probability REAL DEFAULT 0,
    bust_probability REAL DEFAULT 0,
    -- Trends
    sleeper_trending_add INTEGER DEFAULT 0,
    sleeper_trending_drop INTEGER DEFAULT 0,
    -- Metadata
    headshot_url TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weekly player stats
CREATE TABLE IF NOT EXISTS player_weekly_stat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES player(id),
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    fantasy_points REAL DEFAULT 0,
    projected_points REAL DEFAULT 0,
    -- Passing
    pass_yards REAL DEFAULT 0,
    pass_tds INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    -- Rushing
    rush_yards REAL DEFAULT 0,
    rush_tds INTEGER DEFAULT 0,
    carries INTEGER DEFAULT 0,
    -- Receiving
    receptions REAL DEFAULT 0,
    rec_yards REAL DEFAULT 0,
    rec_tds INTEGER DEFAULT 0,
    targets INTEGER DEFAULT 0,
    -- Usage
    snap_count INTEGER DEFAULT 0,
    snap_pct REAL DEFAULT 0,
    target_share REAL DEFAULT 0,
    red_zone_targets INTEGER DEFAULT 0,
    red_zone_carries INTEGER DEFAULT 0,
    -- Weather
    weather_temp INTEGER,
    weather_wind INTEGER,
    weather_condition TEXT,
    UNIQUE(player_id, season, week)
);

-- Roster entries (which players are on which teams)
CREATE TABLE IF NOT EXISTS roster_entry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES team(id),
    player_id INTEGER NOT NULL REFERENCES player(id),
    slot TEXT NOT NULL, -- QB, RB, WR, TE, FLEX, K, DST, BE (bench), IR
    acquisition_type TEXT, -- DRAFT, WAIVER, TRADE, FREE_AGENT
    acquired_date TEXT,
    UNIQUE(team_id, player_id)
);

-- Weekly matchups
CREATE TABLE IF NOT EXISTS matchup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id INTEGER NOT NULL REFERENCES league(id),
    week INTEGER NOT NULL,
    home_team_id INTEGER REFERENCES team(id),
    away_team_id INTEGER REFERENCES team(id),
    home_score REAL,
    away_score REAL,
    home_projected REAL,
    away_projected REAL,
    is_playoff INTEGER DEFAULT 0,
    winner_team_id INTEGER REFERENCES team(id),
    UNIQUE(league_id, week, home_team_id)
);

-- Draft picks
CREATE TABLE IF NOT EXISTS draft_pick (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id INTEGER NOT NULL REFERENCES league(id),
    team_id INTEGER NOT NULL REFERENCES team(id),
    player_id INTEGER NOT NULL REFERENCES player(id),
    round INTEGER NOT NULL,
    pick_number INTEGER NOT NULL,
    overall_pick INTEGER NOT NULL,
    adp REAL, -- Average draft position for comparison
    UNIQUE(league_id, overall_pick)
);

-- NFL team schedule (for strength of schedule)
CREATE TABLE IF NOT EXISTS nfl_team_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nfl_team TEXT NOT NULL,
    week INTEGER NOT NULL,
    opponent TEXT NOT NULL,
    is_home INTEGER DEFAULT 0,
    -- Points allowed by position (for matchup grading)
    pa_qb_rank INTEGER,
    pa_qb_ppg REAL,
    pa_rb_rank INTEGER,
    pa_rb_ppg REAL,
    pa_wr_rank INTEGER,
    pa_wr_ppg REAL,
    pa_te_rank INTEGER,
    pa_te_ppg REAL,
    pa_k_rank INTEGER,
    pa_k_ppg REAL,
    pa_dst_rank INTEGER,
    pa_dst_ppg REAL,
    UNIQUE(nfl_team, week)
);

-- Transaction log
CREATE TABLE IF NOT EXISTS transaction_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id INTEGER NOT NULL REFERENCES league(id),
    team_id INTEGER REFERENCES team(id),
    type TEXT NOT NULL, -- WAIVER, TRADE, FA_ADD, DROP
    player_id INTEGER REFERENCES player(id),
    details TEXT, -- JSON with extra info
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- In-app notifications
CREATE TABLE IF NOT EXISTS notification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    type TEXT NOT NULL, -- LINEUP_ALERT, WAIVER_TIP, INJURY, RECAP, TRADE_SUGGESTION
    priority TEXT DEFAULT 'normal', -- low, normal, high, urgent
    is_read INTEGER DEFAULT 0,
    data TEXT, -- JSON payload
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Claude chat messages
CREATE TABLE IF NOT EXISTS chat_message (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL, -- user, assistant
    content TEXT NOT NULL,
    context_summary TEXT, -- What league data was included
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Optimal lineup (post-game analysis)
CREATE TABLE IF NOT EXISTS optimal_lineup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES team(id),
    week INTEGER NOT NULL,
    actual_points REAL,
    optimal_points REAL,
    points_left_on_bench REAL,
    optimal_roster TEXT, -- JSON: list of player_id + slot
    UNIQUE(team_id, week)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_player_position ON player(position);
CREATE INDEX IF NOT EXISTS idx_player_nfl_team ON player(nfl_team);
CREATE INDEX IF NOT EXISTS idx_player_espn_id ON player(espn_id);
CREATE INDEX IF NOT EXISTS idx_roster_team ON roster_entry(team_id);
CREATE INDEX IF NOT EXISTS idx_roster_player ON roster_entry(player_id);
CREATE INDEX IF NOT EXISTS idx_stat_player_week ON player_weekly_stat(player_id, season, week);
CREATE INDEX IF NOT EXISTS idx_matchup_week ON matchup(league_id, week);
CREATE INDEX IF NOT EXISTS idx_notification_read ON notification(is_read, created_at);
CREATE INDEX IF NOT EXISTS idx_chat_created ON chat_message(created_at);
CREATE INDEX IF NOT EXISTS idx_schedule_team ON nfl_team_schedule(nfl_team, week);
