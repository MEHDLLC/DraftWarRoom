"""
Trade analyzer: evaluates proposed trades by comparing ROS value and roster fit.
"""
from ..database import get_db


async def analyze_trade(
    team_id: int,
    give_player_ids: list[int],
    receive_player_ids: list[int],
) -> dict:
    """
    Analyze a proposed trade and return verdict with explanation.
    """
    db = await get_db()
    try:
        # Get player details for both sides
        give_players = await _get_players(db, give_player_ids)
        receive_players = await _get_players(db, receive_player_ids)

        if not give_players or not receive_players:
            return {
                "give_players": give_players,
                "receive_players": receive_players,
                "give_value": 0,
                "receive_value": 0,
                "verdict": "error",
                "explanation": "Could not find all players in the trade.",
                "roster_impact": "Unknown",
            }

        give_value = sum(p.get("trade_value") or p.get("ros_projection") or 0 for p in give_players)
        receive_value = sum(p.get("trade_value") or p.get("ros_projection") or 0 for p in receive_players)

        # Calculate roster impact
        roster = await db.execute_fetchall("""
            SELECT p.position, p.composite_score
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ?
        """, (team_id,))

        roster_impact = _evaluate_roster_impact(
            [dict(r) for r in roster],
            give_players,
            receive_players,
        )

        # Determine verdict
        diff_pct = ((receive_value - give_value) / max(give_value, 1)) * 100

        if diff_pct > 15:
            verdict = "accept"
            explanation = (
                f"Strong accept. You're gaining {diff_pct:.0f}% more value. "
                f"Receiving side ({receive_value:.1f}) clearly outweighs giving side ({give_value:.1f})."
            )
        elif diff_pct > -5:
            verdict = "fair"
            explanation = (
                f"Fair trade. Values are close (giving {give_value:.1f}, receiving {receive_value:.1f}). "
                f"Decision depends on roster needs."
            )
        else:
            verdict = "reject"
            explanation = (
                f"You'd be giving up {abs(diff_pct):.0f}% more value than you receive. "
                f"Giving side ({give_value:.1f}) outweighs receiving ({receive_value:.1f})."
            )

        return {
            "give_players": give_players,
            "receive_players": receive_players,
            "give_value": round(give_value, 1),
            "receive_value": round(receive_value, 1),
            "verdict": verdict,
            "explanation": explanation,
            "roster_impact": roster_impact,
        }
    finally:
        await db.close()


async def _get_players(db, player_ids: list[int]) -> list[dict]:
    if not player_ids:
        return []
    placeholders = ",".join("?" * len(player_ids))
    rows = await db.execute_fetchall(
        f"SELECT * FROM player WHERE id IN ({placeholders})", player_ids
    )
    return [
        {
            "id": r["id"], "espn_id": r["espn_id"], "full_name": r["full_name"],
            "position": r["position"], "nfl_team": r["nfl_team"],
            "projected_points": r["projected_points"],
            "ros_projection": r["ros_projection"],
            "composite_score": r["composite_score"],
            "trade_value": r["trade_value"],
            "boom_probability": r["boom_probability"],
            "bust_probability": r["bust_probability"],
        }
        for r in rows
    ]


def _evaluate_roster_impact(
    roster: list[dict],
    give: list[dict],
    receive: list[dict],
) -> str:
    """Evaluate how the trade affects roster composition."""
    give_positions = [p["position"] for p in give]
    receive_positions = [p["position"] for p in receive]

    impacts = []

    # Check if trading away depth at a thin position
    pos_counts = {}
    for p in roster:
        pos_counts[p["position"]] = pos_counts.get(p["position"], 0) + 1

    for pos in give_positions:
        count = pos_counts.get(pos, 0)
        if count <= 2:
            impacts.append(f"Warning: trading from thin {pos} depth ({count} on roster)")

    for pos in receive_positions:
        if pos not in give_positions:
            impacts.append(f"Adds {pos} depth")

    if not impacts:
        return "Neutral roster impact."
    return " | ".join(impacts)
