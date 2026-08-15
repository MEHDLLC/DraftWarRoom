"""
Optimal lineup calculator: after games, computes the best possible lineup
and compares to what was actually started. Shows "points left on bench."
"""
import json
from itertools import combinations
from ..database import get_db
from ..utils.constants import FLEX_ELIGIBLE


async def get_optimal_lineup(team_id: int, week: int) -> dict:
    """
    Calculate the optimal lineup for a completed week and compare to actual.
    """
    db = await get_db()
    try:
        # Get all players on roster with their actual points for the week
        rows = await db.execute_fetchall("""
            SELECT p.id, p.full_name, p.position, re.slot,
                   COALESCE(pws.fantasy_points, 0) as actual_points
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            LEFT JOIN player_weekly_stat pws ON pws.player_id = p.id
                AND pws.week = ? AND pws.season = (SELECT season FROM league LIMIT 1)
            WHERE re.team_id = ?
        """, (week, team_id))

        if not rows:
            return {"week": week, "actual_points": 0, "optimal_points": 0,
                    "points_left_on_bench": 0, "optimal_roster": []}

        players = [dict(r) for r in rows]

        # Get slot configuration
        league_row = await db.execute_fetchall("SELECT roster_slots FROM league LIMIT 1")
        if league_row and league_row[0]["roster_slots"]:
            slot_config = json.loads(league_row[0]["roster_slots"])
        else:
            slot_config = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "K": 1, "DST": 1}

        # Calculate actual points (starters only)
        actual_points = sum(
            p["actual_points"] for p in players if p["slot"] not in ("BE", "IR")
        )

        # Find optimal lineup
        by_pos = {}
        for p in players:
            by_pos.setdefault(p["position"], []).append(p)

        # Sort each position by actual points
        for pos in by_pos:
            by_pos[pos].sort(key=lambda x: x["actual_points"], reverse=True)

        optimal_roster = []
        used_ids = set()

        # Fill required slots with best performers
        for pos, count in slot_config.items():
            if pos in ("FLEX", "BE", "IR"):
                continue
            available = [p for p in by_pos.get(pos, []) if p["id"] not in used_ids]
            for p in available[:count]:
                optimal_roster.append({"player_id": p["id"], "player_name": p["full_name"],
                                       "position": p["position"], "slot": pos,
                                       "points": p["actual_points"]})
                used_ids.add(p["id"])

        # Fill FLEX
        flex_count = slot_config.get("FLEX", 0)
        flex_candidates = []
        for pos in FLEX_ELIGIBLE:
            flex_candidates.extend(p for p in by_pos.get(pos, []) if p["id"] not in used_ids)
        flex_candidates.sort(key=lambda x: x["actual_points"], reverse=True)
        for p in flex_candidates[:flex_count]:
            optimal_roster.append({"player_id": p["id"], "player_name": p["full_name"],
                                   "position": p["position"], "slot": "FLEX",
                                   "points": p["actual_points"]})
            used_ids.add(p["id"])

        # Fill K and DST if not in slot_config iteration
        optimal_points = sum(p["points"] for p in optimal_roster)
        points_left = round(optimal_points - actual_points, 2)

        # Save to DB
        await db.execute("""
            INSERT OR REPLACE INTO optimal_lineup (team_id, week, actual_points, optimal_points,
                                                    points_left_on_bench, optimal_roster)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (team_id, week, actual_points, optimal_points, points_left,
              json.dumps(optimal_roster)))
        await db.commit()

        return {
            "week": week,
            "actual_points": round(actual_points, 2),
            "optimal_points": round(optimal_points, 2),
            "points_left_on_bench": points_left,
            "optimal_roster": optimal_roster,
        }
    finally:
        await db.close()
