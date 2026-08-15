"""
Weighted composite scoring engine.
Normalizes multiple factors to 0-100 percentile and produces a single composite score.
"""
from ..utils.constants import SCORE_WEIGHTS


def percentile_rank(value: float, all_values: list[float]) -> float:
    """Calculate percentile rank (0-100) of a value within a distribution."""
    if not all_values or len(all_values) <= 1:
        return 50.0
    sorted_vals = sorted(all_values)
    below = sum(1 for v in sorted_vals if v < value)
    equal = sum(1 for v in sorted_vals if v == value)
    return ((below + 0.5 * equal) / len(sorted_vals)) * 100


def compute_composite_score(
    ros_projection: float,
    all_ros_projections: list[float],
    usage_trend: float,
    all_usage_trends: list[float],
    matchup_score: float,
    all_matchup_scores: list[float],
    injury_score: float,  # 0-100 directly (100 = healthy)
    community_score: float,
    all_community_scores: list[float],
) -> tuple[float, dict]:
    """
    Compute weighted composite score for a player.
    Returns (score, breakdown_dict).
    """
    ros_pct = percentile_rank(ros_projection, all_ros_projections)
    usage_pct = percentile_rank(usage_trend, all_usage_trends)
    matchup_pct = percentile_rank(matchup_score, all_matchup_scores)
    injury_pct = injury_score  # Already 0-100
    community_pct = percentile_rank(community_score, all_community_scores)

    composite = (
        SCORE_WEIGHTS["ros_projection"] * ros_pct
        + SCORE_WEIGHTS["usage_trend"] * usage_pct
        + SCORE_WEIGHTS["matchup_difficulty"] * matchup_pct
        + SCORE_WEIGHTS["injury_status"] * injury_pct
        + SCORE_WEIGHTS["community_signal"] * community_pct
    )

    breakdown = {
        "ros_projection": {"raw": ros_projection, "percentile": round(ros_pct, 1), "weight": SCORE_WEIGHTS["ros_projection"]},
        "usage_trend": {"raw": usage_trend, "percentile": round(usage_pct, 1), "weight": SCORE_WEIGHTS["usage_trend"]},
        "matchup_difficulty": {"raw": matchup_score, "percentile": round(matchup_pct, 1), "weight": SCORE_WEIGHTS["matchup_difficulty"]},
        "injury_status": {"raw": injury_score, "percentile": round(injury_pct, 1), "weight": SCORE_WEIGHTS["injury_status"]},
        "community_signal": {"raw": community_score, "percentile": round(community_pct, 1), "weight": SCORE_WEIGHTS["community_signal"]},
    }

    return round(composite, 2), breakdown


def injury_to_score(status: str | None) -> float:
    """Convert injury status string to a 0-100 score."""
    if not status or status in ("ACTIVE", "NORMAL"):
        return 100.0
    mapping = {
        "PROBABLE": 90.0,
        "QUESTIONABLE": 60.0,
        "DOUBTFUL": 25.0,
        "OUT": 0.0,
        "INJURED_RESERVE": 0.0,
        "SUSPENSION": 0.0,
    }
    return mapping.get(status.upper(), 50.0)


def usage_trend_score(weekly_snaps: list[float]) -> float:
    """
    Calculate weighted usage trend from recent snap percentages.
    More recent weeks weighted higher: [1, 2, 3] for last 3 weeks.
    """
    if not weekly_snaps:
        return 0.0
    recent = weekly_snaps[-3:]  # Last 3 weeks
    weights = list(range(1, len(recent) + 1))
    total_weight = sum(weights)
    return sum(s * w for s, w in zip(recent, weights)) / total_weight


def generate_explanation(breakdown: dict, player_name: str, position: str) -> str:
    """Generate a human-readable explanation of why a player scored the way they did."""
    parts = []

    # Find the strongest factor
    factors = sorted(breakdown.items(), key=lambda x: x[1]["percentile"] * x[1]["weight"], reverse=True)

    for factor_name, data in factors[:3]:
        pct = data["percentile"]
        label = factor_name.replace("_", " ").title()
        if pct >= 80:
            parts.append(f"elite {label.lower()}")
        elif pct >= 60:
            parts.append(f"strong {label.lower()}")
        elif pct <= 20:
            parts.append(f"weak {label.lower()}")

    if parts:
        return f"{player_name} benefits from {', '.join(parts[:2])}."
    return f"{player_name} has an average profile across all factors."
