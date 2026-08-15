"""
Lineup advisor: recommends optimal start/sit decisions for each roster slot.
Uses composite scores to rank players and optimize FLEX selection.
"""
import json
from ..database import get_db
from ..utils.constants import FLEX_ELIGIBLE


async def get_lineup_advice(team_id: int, week: int) -> dict:
    """
    Generate lineup recommendations for a team for a given week.
    Returns starters, bench, and swap suggestions.
    """
    db = await get_db()
    try:
        # Get roster with player scores
        rows = await db.execute_fetchall("""
            SELECT p.id, p.full_name, p.position, p.nfl_team, p.composite_score,
                   p.projected_points, p.boom_probability, p.bust_probability,
                   p.injury_status, p.status, re.slot
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ?
            ORDER BY p.composite_score DESC
        """, (team_id,))

        if not rows:
            return {"week": week, "starters": [], "bench": [], "swap_suggestions": []}

        players = [dict(r) for r in rows]

        # Get league roster slot config
        league_row = await db.execute_fetchall("SELECT roster_slots FROM league LIMIT 1")
        if league_row and league_row[0]["roster_slots"]:
            slot_config = json.loads(league_row[0]["roster_slots"])
        else:
            slot_config = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "K": 1, "DST": 1}

        # Separate by position
        by_pos = {}
        for p in players:
            pos = p["position"]
            by_pos.setdefault(pos, []).append(p)

        # Sort each position group by composite score
        for pos in by_pos:
            by_pos[pos].sort(key=lambda x: x["composite_score"] or 0, reverse=True)

        starters = []
        used_ids = set()

        # Fill required slots
        for pos, count in slot_config.items():
            if pos in ("FLEX", "BE", "IR"):
                continue
            available = [p for p in by_pos.get(pos, []) if p["id"] not in used_ids]
            for p in available[:count]:
                starters.append(_make_recommendation(p, pos))
                used_ids.add(p["id"])

        # Fill FLEX with best remaining FLEX-eligible player
        flex_count = slot_config.get("FLEX", 0)
        flex_candidates = []
        for pos in FLEX_ELIGIBLE:
            flex_candidates.extend(
                p for p in by_pos.get(pos, []) if p["id"] not in used_ids
            )
        flex_candidates.sort(key=lambda x: x["composite_score"] or 0, reverse=True)
        for p in flex_candidates[:flex_count]:
            starters.append(_make_recommendation(p, "FLEX"))
            used_ids.add(p["id"])

        # Everyone else is bench
        bench = [
            _make_recommendation(p, "BE")
            for p in players if p["id"] not in used_ids
        ]

        # Find swap suggestions (bench player scores higher than starter at same position)
        swap_suggestions = _find_swaps(starters, bench)

        return {
            "week": week,
            "starters": starters,
            "bench": bench,
            "swap_suggestions": swap_suggestions,
        }
    finally:
        await db.close()


def _make_recommendation(player: dict, slot: str) -> dict:
    score = player.get("composite_score") or 0
    return {
        "player_id": player["id"],
        "player_name": player["full_name"],
        "position": player["position"],
        "nfl_team": player.get("nfl_team"),
        "recommended_slot": slot,
        "composite_score": score,
        "projected_points": player.get("projected_points", 0),
        "boom_probability": player.get("boom_probability", 0),
        "bust_probability": player.get("bust_probability", 0),
        "injury_status": player.get("injury_status"),
        "explanation": _generate_start_sit_reason(player, slot),
        "matchup_grade": _score_to_grade(score),
    }


def _generate_start_sit_reason(player: dict, slot: str) -> str:
    name = player["full_name"]
    score = player.get("composite_score") or 0
    injury = player.get("injury_status")

    if slot == "BE":
        if injury and injury not in ("ACTIVE", "NORMAL"):
            return f"{name} is {injury} — keep on bench until status clears."
        return f"{name} is behind your starters at {player['position']} this week."

    if score >= 80:
        return f"{name} is a must-start with a top-tier composite score."
    elif score >= 60:
        return f"{name} is a solid start this week with above-average metrics."
    elif score >= 40:
        return f"{name} is a borderline start — consider matchup carefully."
    else:
        return f"{name} has concerning metrics this week. Look for alternatives."


def _find_swaps(starters: list[dict], bench: list[dict]) -> list[dict]:
    """Find cases where a bench player should start over a starter."""
    swaps = []
    for bench_p in bench:
        for starter in starters:
            # Same position or both FLEX-eligible for a FLEX slot
            same_pos = bench_p["position"] == starter["position"]
            flex_swap = (
                starter["recommended_slot"] == "FLEX"
                and bench_p["position"] in FLEX_ELIGIBLE
            )
            if (same_pos or flex_swap) and bench_p["composite_score"] > starter["composite_score"]:
                swaps.append({
                    "bench_player": bench_p["player_name"],
                    "bench_score": bench_p["composite_score"],
                    "starter_player": starter["player_name"],
                    "starter_score": starter["composite_score"],
                    "reason": (
                        f"Consider starting {bench_p['player_name']} "
                        f"(score: {bench_p['composite_score']:.0f}) over "
                        f"{starter['player_name']} (score: {starter['composite_score']:.0f})"
                    ),
                })
    return swaps


def _score_to_grade(score: float) -> str:
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B+"
    elif score >= 60:
        return "B"
    elif score >= 50:
        return "C+"
    elif score >= 40:
        return "C"
    elif score >= 30:
        return "D"
    else:
        return "F"
