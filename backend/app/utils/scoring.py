"""Scoring helpers for PPR fantasy football."""

# Standard PPR scoring
PPR_SCORING = {
    "passing_yards": 0.04,    # 1 point per 25 yards
    "passing_tds": 4.0,
    "interceptions": -2.0,
    "rushing_yards": 0.1,     # 1 point per 10 yards
    "rushing_tds": 6.0,
    "receptions": 1.0,        # PPR
    "receiving_yards": 0.1,
    "receiving_tds": 6.0,
    "fumbles_lost": -2.0,
    "two_point_conversions": 2.0,
}


def calculate_fantasy_points(stats: dict, scoring: dict = None) -> float:
    """Calculate fantasy points from a stat line."""
    if scoring is None:
        scoring = PPR_SCORING

    points = 0.0
    for stat, multiplier in scoring.items():
        points += (stats.get(stat, 0) or 0) * multiplier

    return round(points, 2)


def matchup_grade(rank: int | None, num_teams: int = 32) -> str:
    """Convert a points-allowed rank to a letter grade."""
    if rank is None:
        return "C"
    pct = rank / num_teams
    if pct <= 0.125:
        return "A+"
    elif pct <= 0.25:
        return "A"
    elif pct <= 0.375:
        return "B+"
    elif pct <= 0.5:
        return "B"
    elif pct <= 0.625:
        return "C+"
    elif pct <= 0.75:
        return "C"
    elif pct <= 0.875:
        return "D"
    else:
        return "F"
