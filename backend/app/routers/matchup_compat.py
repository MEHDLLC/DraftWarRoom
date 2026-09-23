"""
Frontend-facing matchup endpoints (singular /matchup prefix).

The frontend was written against a `/matchup/*` contract with camelCase
shapes (client.ts Matchup / MatchupAnalysis) centered on the USER's
matchup; the original `/matchups/*` router serves the whole league in
snake_case. This router adapts the same data to what the pages expect.
"""
import math

from fastapi import APIRouter, HTTPException, Query

from ..database import get_db

router = APIRouter()


async def _user_matchup(db, week: int) -> dict:
    """Fetch the user's matchup for a week, shaped as client.ts Matchup."""
    team_rows = await db.execute_fetchall(
        "SELECT id FROM team WHERE is_user_team = 1 LIMIT 1"
    )
    if not team_rows:
        raise HTTPException(status_code=404, detail="User team not identified")
    team_id = team_rows[0]["id"]

    rows = await db.execute_fetchall("""
        SELECT m.*, th.team_name AS home_name, ta.team_name AS away_name
        FROM matchup m
        JOIN team th ON th.id = m.home_team_id
        JOIN team ta ON ta.id = m.away_team_id
        WHERE m.week = ? AND (m.home_team_id = ? OR m.away_team_id = ?)
        LIMIT 1
    """, (week, team_id, team_id))
    if not rows:
        raise HTTPException(status_code=404, detail=f"No matchup found for week {week}")
    m = dict(rows[0])

    home_proj = m.get("home_projected") or 0
    away_proj = m.get("away_projected") or 0
    # Same logistic model as the matchup analyzer (std dev ~20 pts)
    diff = home_proj - away_proj
    home_win = 1 / (1 + math.exp(-diff / (20.0 * 0.55))) if (home_proj or away_proj) else 0.5

    is_home = m["home_team_id"] == team_id
    user_win = home_win if is_home else 1 - home_win

    def side(team_db_id, name, projected, score):
        return {
            "id": str(team_db_id),
            "name": name,
            "projectedScore": projected or 0,
            "actualScore": score,
        }

    return {
        "week": m["week"],
        "homeTeam": side(m["home_team_id"], m["home_name"], home_proj, m.get("home_score")),
        "awayTeam": side(m["away_team_id"], m["away_name"], away_proj, m.get("away_score")),
        "winProbability": round(user_win * 100, 1),
        "matchupId": m["id"],
    }


async def _current_week(db) -> int:
    rows = await db.execute_fetchall("SELECT current_week FROM league LIMIT 1")
    if not rows:
        raise HTTPException(status_code=404, detail="League not synced yet")
    return rows[0]["current_week"]


@router.get("/current")
async def get_current_matchup():
    """The user's matchup for the current week."""
    db = await get_db()
    try:
        week = await _current_week(db)
        return await _user_matchup(db, week)
    finally:
        await db.close()


@router.get("/week/{week}")
async def get_matchup_by_week(week: int):
    """The user's matchup for a specific week."""
    db = await get_db()
    try:
        return await _user_matchup(db, week)
    finally:
        await db.close()


@router.get("/analysis")
async def get_matchup_analysis(week: int | None = Query(None)):
    """Analysis of the user's matchup (client.ts MatchupAnalysis shape)."""
    db = await get_db()
    try:
        target_week = week or await _current_week(db)
        matchup = await _user_matchup(db, target_week)
    finally:
        await db.close()

    key_players: list[str] = []
    analysis_text = ""
    try:
        from ..engine.matchup_analyzer import analyze_matchup
        detail = await analyze_matchup(matchup["matchupId"])
        if "error" not in detail:
            key_players = [
                p.get("full_name", "")
                for p in detail.get("swing_players", [])
                if p.get("full_name")
            ]
            home, away = matchup["homeTeam"], matchup["awayTeam"]
            analysis_text = (
                f"{home['name']} projects {home['projectedScore']:.1f} vs "
                f"{away['name']}'s {away['projectedScore']:.1f}. "
                f"Win probability for your team: {matchup['winProbability']:.0f}%."
            )
            if key_players:
                analysis_text += f" Swing players: {', '.join(key_players[:3])}."
    except Exception:
        pass

    return {
        "week": matchup["week"],
        "matchup": matchup,
        "keyPlayers": key_players,
        "analysis": analysis_text,
        "winProbability": matchup["winProbability"],
    }
