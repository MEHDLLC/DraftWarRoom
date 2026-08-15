"""
Matchup analyzer: win probability, projected scores, swing players.
"""
import math
from ..database import get_db


async def analyze_matchup(matchup_id: int) -> dict:
    """Analyze a matchup with projected scores and win probability."""
    db = await get_db()
    try:
        matchup = await db.execute_fetchall("SELECT * FROM matchup WHERE id = ?", (matchup_id,))
        if not matchup:
            return {"error": "Matchup not found"}
        m = dict(matchup[0])

        # Get roster projections for both teams
        home_proj = await _team_projection(db, m["home_team_id"])
        away_proj = await _team_projection(db, m["away_team_id"])

        # Win probability using normal distribution assumption
        # Standard deviation of weekly fantasy scores ~20 points
        std_dev = 20.0
        diff = home_proj["total"] - away_proj["total"]
        # Using logistic approximation
        home_win_prob = 1 / (1 + math.exp(-diff / (std_dev * 0.55)))

        # Find swing players (players whose boom/bust most affects outcome)
        all_players = home_proj["players"] + away_proj["players"]
        swing_players = sorted(
            all_players,
            key=lambda p: (p.get("boom_probability", 0) + p.get("bust_probability", 0)) * p.get("projected_points", 0),
            reverse=True,
        )[:3]

        return {
            "matchup_id": matchup_id,
            "week": m["week"],
            "home_team_id": m["home_team_id"],
            "away_team_id": m["away_team_id"],
            "home_projected": round(home_proj["total"], 1),
            "away_projected": round(away_proj["total"], 1),
            "home_win_probability": round(home_win_prob * 100, 1),
            "away_win_probability": round((1 - home_win_prob) * 100, 1),
            "swing_players": swing_players,
            "home_roster": home_proj["players"],
            "away_roster": away_proj["players"],
        }
    finally:
        await db.close()


async def _team_projection(db, team_id: int) -> dict:
    """Calculate total projected score for a team's starters."""
    rows = await db.execute_fetchall("""
        SELECT p.id, p.full_name, p.position, p.projected_points,
               p.composite_score, p.boom_probability, p.bust_probability,
               re.slot
        FROM roster_entry re
        JOIN player p ON p.id = re.player_id
        WHERE re.team_id = ? AND re.slot NOT IN ('BE', 'IR')
    """, (team_id,))

    players = [dict(r) for r in rows]
    total = sum(p.get("projected_points") or 0 for p in players)
    return {"total": total, "players": players}
