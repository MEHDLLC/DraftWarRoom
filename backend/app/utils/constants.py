# ESPN position slot mapping
POSITION_SLOTS = {
    0: "QB", 2: "RB", 4: "WR", 6: "TE",
    16: "DST", 17: "K", 20: "BE", 21: "IR", 23: "FLEX"
}

SLOT_TO_ID = {v: k for k, v in POSITION_SLOTS.items()}

# Positions for scoring
OFFENSIVE_POSITIONS = ["QB", "RB", "WR", "TE", "K", "DST"]
FLEX_ELIGIBLE = ["RB", "WR", "TE"]

# Composite score weights
SCORE_WEIGHTS = {
    "ros_projection": 0.30,
    "usage_trend": 0.25,
    "matchup_difficulty": 0.20,
    "injury_status": 0.15,
    "community_signal": 0.10,
}

# Power ranking weights
POWER_RANK_WEIGHTS = {
    "points_for": 0.40,
    "recent_3wk_avg": 0.30,
    "roster_strength": 0.20,
    "record": 0.10,
}

# Boom/bust thresholds
BOOM_MULTIPLIER = 1.5  # > 1.5x average = boom week
BUST_MULTIPLIER = 0.5  # < 0.5x average = bust week

# Scheduler cron expressions
SCHEDULE = {
    "league_sync": {"hour": "*/6"},                     # Every 6 hours
    "sunday_updates": {"day_of_week": "sun", "hour": "8-23"},  # Hourly on Sundays
    "tuesday_waivers": {"day_of_week": "tue", "hour": "6"},    # Tuesday morning
    "thursday_lineup": {"day_of_week": "thu", "hour": "10"},   # Thursday morning
    "monday_recap": {"day_of_week": "mon", "hour": "8"},       # Monday morning
}

# ESPN API constants
ESPN_BASE_URL = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"
ESPN_PLAYER_LIMIT = 1000
