"""
Playoff planner: evaluates weeks 15-17 matchup strength for roster players.
"""
from ..database import get_db


async def get_playoff_analysis(team_id: int) -> dict:
    """Analyze playoff schedule strength for a team's roster."""
    db = await get_db()
    try:
        league_row = await db.execute_fetchall("SELECT playoff_start_week FROM league LIMIT 1")
        playoff_start = league_row[0]["playoff_start_week"] if league_row else 15
        playoff_weeks = [playoff_start, playoff_start + 1, playoff_start + 2]

        roster = await db.execute_fetchall("""
            SELECT p.id, p.full_name, p.position, p.nfl_team, p.composite_score,
                   p.ros_projection, re.slot
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ?
        """, (team_id,))

        player_schedules = []
        for player in roster:
            p = dict(player)
            if not p["nfl_team"] or p["position"] == "DST":
                player_schedules.append({**p, "playoff_matchups": [], "playoff_grade": "N/A"})
                continue

            matchups = []
            for week in playoff_weeks:
                sched = await db.execute_fetchall("""
                    SELECT * FROM nfl_team_schedule
                    WHERE nfl_team = ? AND week = ?
                """, (p["nfl_team"], week))
                if sched:
                    s = dict(sched[0])
                    pos_lower = p["position"].lower()
                    rank_key = f"pa_{pos_lower}_rank"
                    ppg_key = f"pa_{pos_lower}_ppg"
                    matchups.append({
                        "week": week,
                        "opponent": s["opponent"],
                        "is_home": bool(s["is_home"]),
                        "pa_rank": s.get(rank_key),
                        "pa_ppg": s.get(ppg_key),
                        "grade": _rank_to_grade(s.get(rank_key)),
                    })
                else:
                    matchups.append({"week": week, "opponent": "BYE", "grade": "N/A"})

            # Average grade
            grades = [m["grade"] for m in matchups if m["grade"] != "N/A"]
            avg_grade = _average_grade(grades) if grades else "N/A"

            player_schedules.append({
                **p,
                "playoff_matchups": matchups,
                "playoff_grade": avg_grade,
            })

        # Sort by playoff grade (best first)
        grade_order = {"A+": 0, "A": 1, "B+": 2, "B": 3, "C": 4, "D": 5, "F": 6, "N/A": 7}
        player_schedules.sort(key=lambda x: grade_order.get(x["playoff_grade"], 7))

        return {
            "playoff_weeks": playoff_weeks,
            "players": player_schedules,
        }
    finally:
        await db.close()


def _rank_to_grade(rank: int | None) -> str:
    if rank is None:
        return "N/A"
    if rank <= 4:
        return "A+"
    elif rank <= 8:
        return "A"
    elif rank <= 12:
        return "B+"
    elif rank <= 16:
        return "B"
    elif rank <= 22:
        return "C"
    elif rank <= 28:
        return "D"
    else:
        return "F"


def _average_grade(grades: list[str]) -> str:
    grade_values = {"A+": 6, "A": 5, "B+": 4, "B": 3, "C": 2, "D": 1, "F": 0}
    total = sum(grade_values.get(g, 3) for g in grades)
    avg = total / len(grades)
    if avg >= 5.5:
        return "A+"
    elif avg >= 4.5:
        return "A"
    elif avg >= 3.5:
        return "B+"
    elif avg >= 2.5:
        return "B"
    elif avg >= 1.5:
        return "C"
    elif avg >= 0.5:
        return "D"
    else:
        return "F"
