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

# Injury statuses that make a player unplayable this week.
# Includes both ESPN spellings ("INJURY_RESERVE") and ours ("INJURED_RESERVE").
UNAVAILABLE_STATUSES = ("OUT", "INJURED_RESERVE", "INJURY_RESERVE", "SUSPENSION")

# NFL team abbreviations: canonical form is ESPN's (player.nfl_team comes from
# espn_api proTeam). nflverse and Sleeper use slightly different codes.
_TEAM_TO_ESPN = {
    "LA": "LAR",    # nflverse uses LA for the Rams
    "WAS": "WSH",   # nflverse/Sleeper use WAS for Washington
    "JAC": "JAX",
    "OAK": "LV",
    "SD": "LAC",
    "STL": "LAR",
}


def normalize_nfl_team(team: str | None) -> str | None:
    """Normalize an NFL team abbreviation to ESPN's canonical form."""
    if not team:
        return team
    team = team.upper()
    return _TEAM_TO_ESPN.get(team, team)


def normalize_position(position: str | None) -> str | None:
    """Normalize a position code (espn_api reports defenses as 'D/ST')."""
    if not position:
        return position
    return "DST" if position in ("D/ST", "DEF") else position


# Sleeper injury statuses ("Out", "IR", "Sus", ...) -> ESPN-style codes.
_SLEEPER_INJURY_TO_ESPN = {
    "QUESTIONABLE": "QUESTIONABLE",
    "DOUBTFUL": "DOUBTFUL",
    "OUT": "OUT",
    "IR": "INJURED_RESERVE",
    "PUP": "INJURED_RESERVE",
    "SUS": "SUSPENSION",
}


def normalize_injury_status(status: str | None) -> str | None:
    """Normalize a Sleeper/ESPN injury status to the app's canonical codes."""
    if not status:
        return None
    upper = status.upper()
    if upper == "INJURY_RESERVE":
        return "INJURED_RESERVE"
    return _SLEEPER_INJURY_TO_ESPN.get(upper, upper)
