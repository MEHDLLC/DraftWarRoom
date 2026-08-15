"""
Power rankings: weighted composite team rankings beyond W-L record.
0.4*points_for + 0.3*recent_3wk_avg + 0.2*roster_strength + 0.1*record
"""
from ..database import get_db
from .scorer import percentile_rank
from ..utils.constants import POWER_RANK_WEIGHTS


async def calculate_power_rankings() -> list[dict]:
    """Calculate and update power rankings for all teams."""
    db = await get_db()
    try:
        teams = await db.execute_fetchall("SELECT * FROM team")
        if not teams:
            return []

        teams = [dict(t) for t in teams]
        league_row = await db.execute_fetchall("SELECT current_week, id FROM league LIMIT 1")
        if not league_row:
            return []
        current_week = league_row[0]["current_week"]
        league_id = league_row[0]["id"]

        # Gather data for percentile calculations
        all_pf = [t["points_for"] for t in teams]
        all_records = []
        all_recent = []
        all_roster_str = []

        for team in teams:
            # Record as win%
            total_games = team["wins"] + team["losses"] + team["ties"]
            win_pct = (team["wins"] + 0.5 * team["ties"]) / max(total_games, 1)
            all_records.append(win_pct)
            team["_win_pct"] = win_pct

            # Recent 3-week average
            recent = await db.execute_fetchall("""
                SELECT CASE
                    WHEN home_team_id = ? THEN home_score
                    ELSE away_score
                END as score
                FROM matchup
                WHERE (home_team_id = ? OR away_team_id = ?)
                AND week <= ? AND (home_score IS NOT NULL)
                ORDER BY week DESC LIMIT 3
            """, (team["id"], team["id"], team["id"], current_week))
            recent_scores = [r["score"] for r in recent if r["score"] is not None]
            recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
            all_recent.append(recent_avg)
            team["_recent_avg"] = recent_avg

            # Roster strength (average composite score of starters)
            starters = await db.execute_fetchall("""
                SELECT p.composite_score
                FROM roster_entry re
                JOIN player p ON p.id = re.player_id
                WHERE re.team_id = ? AND re.slot NOT IN ('BE', 'IR')
            """, (team["id"],))
            scores = [s["composite_score"] for s in starters if s["composite_score"]]
            roster_str = sum(scores) / len(scores) if scores else 0
            all_roster_str.append(roster_str)
            team["_roster_str"] = roster_str

        # Calculate composite power ranking
        for team in teams:
            pf_pct = percentile_rank(team["points_for"], all_pf)
            recent_pct = percentile_rank(team["_recent_avg"], all_recent)
            roster_pct = percentile_rank(team["_roster_str"], all_roster_str)
            record_pct = percentile_rank(team["_win_pct"], all_records)

            power_score = (
                POWER_RANK_WEIGHTS["points_for"] * pf_pct
                + POWER_RANK_WEIGHTS["recent_3wk_avg"] * recent_pct
                + POWER_RANK_WEIGHTS["roster_strength"] * roster_pct
                + POWER_RANK_WEIGHTS["record"] * record_pct
            )
            team["power_rank_score"] = round(power_score, 2)

            # Update in DB
            await db.execute(
                "UPDATE team SET power_rank_score = ? WHERE id = ?",
                (team["power_rank_score"], team["id"]),
            )

        await db.commit()

        # Sort and return
        teams.sort(key=lambda t: t["power_rank_score"], reverse=True)
        return [
            {
                "rank": i + 1,
                "team_id": t["id"],
                "team_name": t["team_name"],
                "owner_name": t["owner_name"],
                "score": t["power_rank_score"],
                "points_for": t["points_for"],
                "record": f"{t['wins']}-{t['losses']}",
            }
            for i, t in enumerate(teams)
        ]
    finally:
        await db.close()
