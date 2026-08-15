"""
Boom/bust probability calculator.
Boom = weeks where player exceeded 1.5x their average.
Bust = weeks where player scored below 0.5x their average.
"""
from ..utils.constants import BOOM_MULTIPLIER, BUST_MULTIPLIER


def calculate_boom_bust(weekly_points: list[float]) -> tuple[float, float]:
    """
    Calculate boom and bust probabilities from weekly scoring history.
    Returns (boom_probability, bust_probability) as 0-100 percentages.
    """
    if len(weekly_points) < 3:
        return 0.0, 0.0

    # Filter out zero weeks (bye/injury) for average calculation
    active_weeks = [p for p in weekly_points if p > 0]
    if len(active_weeks) < 3:
        return 0.0, 0.0

    avg = sum(active_weeks) / len(active_weeks)
    if avg <= 0:
        return 0.0, 0.0

    boom_threshold = avg * BOOM_MULTIPLIER
    bust_threshold = avg * BUST_MULTIPLIER

    boom_weeks = sum(1 for p in active_weeks if p >= boom_threshold)
    bust_weeks = sum(1 for p in active_weeks if p <= bust_threshold)

    boom_pct = (boom_weeks / len(active_weeks)) * 100
    bust_pct = (bust_weeks / len(active_weeks)) * 100

    return round(boom_pct, 1), round(bust_pct, 1)


def boom_bust_label(boom: float, bust: float) -> str:
    """Return a human-readable label for boom/bust profile."""
    if boom >= 30 and bust <= 15:
        return "High Ceiling"
    elif boom >= 25:
        return "Boom-or-Bust"
    elif bust >= 30:
        return "Inconsistent"
    elif boom <= 10 and bust <= 10:
        return "Steady Floor"
    elif bust <= 15:
        return "Reliable"
    else:
        return "Average"
