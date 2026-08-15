from fastapi import APIRouter, HTTPException
from ..database import get_db
from ..schemas.models import MatchupInfo, TeamInfo

router = APIRouter()


def _build_team(r, prefix: str) -> TeamInfo:
    """Build a TeamInfo from a joined matchup+team row using column prefix."""
    return TeamInfo(
        id=r[f"{prefix}_id"],
        espn_team_id=r[f"{prefix}_espn_team_id"],
        team_name=r[f"{prefix}_team_name"],
        owner_name=r[f"{prefix}_owner_name"],
        wins=r[f"{prefix}_wins"],
        losses=r[f"{prefix}_losses"],
        ties=r[f"{prefix}_ties"],
        points_for=r[f"{prefix}_points_for"],
        points_against=r[f"{prefix}_points_against"],
        is_user_team=bool(r[f"{prefix}_is_user_team"]),
        power_rank_score=r[f"{prefix}_power_rank_score"],
        playoff_probability=r[f"{prefix}_playoff_probability"],
    )


MATCHUP_QUERY = """
    SELECT
        m.id, m.week, m.home_score, m.away_score,
        m.home_projected, m.away_projected,
        ht.id AS home_id, ht.espn_team_id AS home_espn_team_id,
        ht.team_name AS home_team_name, ht.owner_name AS home_owner_name,
        ht.wins AS home_wins, ht.losses AS home_losses, ht.ties AS home_ties,
        ht.points_for AS home_points_for, ht.points_against AS home_points_against,
        ht.is_user_team AS home_is_user_team,
        ht.power_rank_score AS home_power_rank_score,
        ht.playoff_probability AS home_playoff_probability,
        at2.id AS away_id, at2.espn_team_id AS away_espn_team_id,
        at2.team_name AS away_team_name, at2.owner_name AS away_owner_name,
        at2.wins AS away_wins, at2.losses AS away_losses, at2.ties AS away_ties,
        at2.points_for AS away_points_for, at2.points_against AS away_points_against,
        at2.is_user_team AS away_is_user_team,
        at2.power_rank_score AS away_power_rank_score,
        at2.playoff_probability AS away_playoff_probability
    FROM matchup m
    JOIN team ht ON ht.id = m.home_team_id
    JOIN team at2 ON at2.id = m.away_team_id
"""


def _build_matchup(r) -> MatchupInfo:
    home_team = _build_team(r, "home")
    away_team = _build_team(r, "away")

    # Simple win-probability estimate based on projected scores
    win_probability = None
    if r["home_projected"] and r["away_projected"]:
        total = r["home_projected"] + r["away_projected"]
        if total > 0:
            win_probability = round(r["home_projected"] / total, 3)

    return MatchupInfo(
        week=r["week"],
        home_team=home_team,
        away_team=away_team,
        home_score=r["home_score"],
        away_score=r["away_score"],
        home_projected=r["home_projected"],
        away_projected=r["away_projected"],
        win_probability=win_probability,
    )


@router.get("/current", response_model=list[MatchupInfo])
async def get_current_matchups():
    """Get matchups for the current week."""
    db = await get_db()
    try:
        league_rows = await db.execute_fetchall("SELECT current_week FROM league LIMIT 1")
        if not league_rows:
            raise HTTPException(status_code=404, detail="League not synced yet")
        current_week = league_rows[0]["current_week"]

        rows = await db.execute_fetchall(
            MATCHUP_QUERY + " WHERE m.week = ? ORDER BY m.id",
            (current_week,),
        )
        return [_build_matchup(r) for r in rows]
    finally:
        await db.close()


@router.get("/week/{week}", response_model=list[MatchupInfo])
async def get_week_matchups(week: int):
    """Get matchups for a specific week."""
    if week < 1 or week > 18:
        raise HTTPException(status_code=400, detail="Week must be between 1 and 18")
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            MATCHUP_QUERY + " WHERE m.week = ? ORDER BY m.id",
            (week,),
        )
        if not rows:
            raise HTTPException(status_code=404, detail=f"No matchups found for week {week}")
        return [_build_matchup(r) for r in rows]
    finally:
        await db.close()


@router.get("/analysis/{matchup_id}")
async def get_matchup_analysis(matchup_id: int):
    """Get detailed matchup analysis including roster comparisons."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            MATCHUP_QUERY + " WHERE m.id = ?",
            (matchup_id,),
        )
        if not rows:
            raise HTTPException(status_code=404, detail=f"Matchup {matchup_id} not found")

        r = rows[0]
        matchup = _build_matchup(r)

        # Get rosters for both teams with player details
        home_roster = await db.execute_fetchall(
            """
            SELECT p.full_name, p.position, p.projected_points, p.composite_score,
                   p.boom_probability, p.bust_probability, re.slot
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ?
            ORDER BY CASE re.slot
                WHEN 'QB' THEN 1 WHEN 'RB' THEN 2 WHEN 'WR' THEN 3
                WHEN 'TE' THEN 4 WHEN 'FLEX' THEN 5 WHEN 'K' THEN 6
                WHEN 'DST' THEN 7 WHEN 'BE' THEN 8 WHEN 'IR' THEN 9
            END
            """,
            (r["home_id"],),
        )

        away_roster = await db.execute_fetchall(
            """
            SELECT p.full_name, p.position, p.projected_points, p.composite_score,
                   p.boom_probability, p.bust_probability, re.slot
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ?
            ORDER BY CASE re.slot
                WHEN 'QB' THEN 1 WHEN 'RB' THEN 2 WHEN 'WR' THEN 3
                WHEN 'TE' THEN 4 WHEN 'FLEX' THEN 5 WHEN 'K' THEN 6
                WHEN 'DST' THEN 7 WHEN 'BE' THEN 8 WHEN 'IR' THEN 9
            END
            """,
            (r["away_id"],),
        )

        def _format_roster(roster_rows):
            return [
                {
                    "name": pr["full_name"],
                    "position": pr["position"],
                    "slot": pr["slot"],
                    "projected_points": pr["projected_points"] or 0,
                    "composite_score": pr["composite_score"] or 0,
                    "boom_probability": pr["boom_probability"] or 0,
                    "bust_probability": pr["bust_probability"] or 0,
                }
                for pr in roster_rows
            ]

        # Position-by-position advantage analysis
        position_advantages = []
        for pos in ["QB", "RB", "WR", "TE", "FLEX", "K", "DST"]:
            home_starters = [
                p for p in home_roster
                if p["slot"] == pos
            ]
            away_starters = [
                p for p in away_roster
                if p["slot"] == pos
            ]
            home_proj = sum(p["projected_points"] or 0 for p in home_starters)
            away_proj = sum(p["projected_points"] or 0 for p in away_starters)
            if home_proj > 0 or away_proj > 0:
                diff = home_proj - away_proj
                advantage = matchup.home_team.team_name if diff > 0 else matchup.away_team.team_name
                position_advantages.append({
                    "position": pos,
                    "home_projected": round(home_proj, 1),
                    "away_projected": round(away_proj, 1),
                    "advantage": advantage,
                    "margin": round(abs(diff), 1),
                })

        return {
            "matchup": matchup,
            "home_roster": _format_roster(home_roster),
            "away_roster": _format_roster(away_roster),
            "position_advantages": position_advantages,
        }
    finally:
        await db.close()
