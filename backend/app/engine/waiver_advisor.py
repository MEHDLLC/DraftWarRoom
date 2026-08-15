"""
Waiver wire advisor: scores free agents and suggests pickups with drop candidates.
"""
from ..database import get_db


async def get_waiver_recommendations(team_id: int, limit: int = 20) -> list[dict]:
    """
    Get ranked waiver wire recommendations for a team.
    Considers roster needs, player composite scores, and suggests who to drop.
    """
    db = await get_db()
    try:
        # Get user's current roster
        roster = await db.execute_fetchall("""
            SELECT p.id, p.full_name, p.position, p.composite_score, p.trade_value
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ?
        """, (team_id,))
        roster_players = [dict(r) for r in roster]

        # Count positions on roster
        pos_counts = {}
        for p in roster_players:
            pos_counts[p["position"]] = pos_counts.get(p["position"], 0) + 1

        # Get free agents sorted by composite score
        free_agents = await db.execute_fetchall("""
            SELECT p.* FROM player p
            WHERE p.id NOT IN (SELECT player_id FROM roster_entry)
            AND p.position IN ('QB', 'RB', 'WR', 'TE', 'K', 'DST')
            AND p.composite_score > 0
            ORDER BY p.composite_score DESC
            LIMIT ?
        """, (limit * 2,))

        recommendations = []
        for fa in free_agents:
            fa = dict(fa)
            pos = fa["position"]

            # Calculate need score (higher if position is thin on roster)
            ideal = {"QB": 2, "RB": 5, "WR": 5, "TE": 2, "K": 1, "DST": 1}
            current = pos_counts.get(pos, 0)
            need_bonus = max(0, (ideal.get(pos, 2) - current) * 5)

            # Find worst player at same position on roster (potential drop)
            same_pos = sorted(
                [p for p in roster_players if p["position"] == pos],
                key=lambda x: x["composite_score"] or 0,
            )
            suggested_drop = None
            drop_explanation = None
            if same_pos and (fa["composite_score"] or 0) > (same_pos[0]["composite_score"] or 0):
                suggested_drop = same_pos[0]
                drop_explanation = (
                    f"{same_pos[0]['full_name']} is your weakest {pos} "
                    f"(score: {same_pos[0]['composite_score']:.0f})"
                )

            explanation = _waiver_explanation(fa, need_bonus, pos, current)

            recommendations.append({
                "player": {
                    "id": fa["id"],
                    "espn_id": fa.get("espn_id"),
                    "full_name": fa["full_name"],
                    "position": fa["position"],
                    "nfl_team": fa.get("nfl_team"),
                    "composite_score": fa.get("composite_score", 0),
                    "projected_points": fa.get("projected_points", 0),
                    "boom_probability": fa.get("boom_probability", 0),
                    "bust_probability": fa.get("bust_probability", 0),
                    "sleeper_trending_add": fa.get("sleeper_trending_add", 0),
                    "injury_status": fa.get("injury_status"),
                    "headshot_url": fa.get("headshot_url"),
                },
                "composite_score": (fa.get("composite_score") or 0) + need_bonus,
                "explanation": explanation,
                "suggested_drop": suggested_drop,
                "drop_explanation": drop_explanation,
            })

        # Sort by adjusted score and limit
        recommendations.sort(key=lambda x: x["composite_score"], reverse=True)
        return recommendations[:limit]
    finally:
        await db.close()


def _waiver_explanation(player: dict, need_bonus: float, position: str, roster_count: int) -> str:
    parts = []
    score = player.get("composite_score") or 0
    trending = player.get("sleeper_trending_add") or 0

    if score >= 70:
        parts.append(f"Top-tier free agent with a composite score of {score:.0f}")
    elif score >= 50:
        parts.append(f"Solid pickup option (score: {score:.0f})")
    else:
        parts.append(f"Speculative add (score: {score:.0f})")

    if need_bonus > 0:
        parts.append(f"fills a roster need at {position}")

    if trending >= 1000:
        parts.append(f"trending heavily ({trending:,} adds)")
    elif trending >= 100:
        parts.append(f"gaining traction ({trending:,} adds)")

    return ". ".join(parts) + "."
