from fastapi import APIRouter, HTTPException
from ..database import get_db
from ..schemas.models import LeagueInfo, TeamInfo
from ..jobs.sync_league import sync_league_data

router = APIRouter()


def _team_payload(r, rank: int) -> dict:
    """Shape a team row the way the frontend expects (see client.ts Team)."""
    return {
        "id": str(r["id"]),
        "name": r["team_name"],
        "owner": r["owner_name"] or "",
        "record": {"wins": r["wins"], "losses": r["losses"], "ties": r["ties"]},
        "pointsFor": r["points_for"] or 0,
        "pointsAgainst": r["points_against"] or 0,
        "rank": rank,
        "isUserTeam": bool(r["is_user_team"]),
    }


@router.get("")
async def get_league_root():
    """League summary in the shape the frontend's LeagueContext expects."""
    db = await get_db()
    try:
        row = await db.execute_fetchall("SELECT * FROM league LIMIT 1")
        if not row:
            raise HTTPException(status_code=404, detail="League not synced yet. POST /api/v1/league/sync first.")
        r = row[0]
        team_row = await db.execute_fetchall(
            "SELECT id FROM team WHERE is_user_team = 1 LIMIT 1"
        )
        return {
            "id": str(r["id"]),
            "name": r["name"],
            "platform": "ESPN",
            "season": r["season"],
            "week": r["current_week"],
            "teamCount": r["num_teams"],
            "scoringType": r["scoring_type"] or "PPR",
            "userTeamId": str(team_row[0]["id"]) if team_row else "",
        }
    finally:
        await db.close()


@router.post("/sync")
async def trigger_sync():
    """Trigger a full league data sync from ESPN."""
    try:
        await sync_league_data()
        return {"status": "ok", "message": "League sync completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set-user-team/{team_id}")
async def set_user_team(team_id: int):
    """Mark a team as the user's team."""
    db = await get_db()
    try:
        await db.execute("UPDATE team SET is_user_team = 0")
        result = await db.execute("UPDATE team SET is_user_team = 1 WHERE id = ?", (team_id,))
        await db.commit()
        row = await db.execute_fetchall("SELECT team_name FROM team WHERE id = ?", (team_id,))
        if not row:
            raise HTTPException(status_code=404, detail="Team not found")
        return {"status": "ok", "message": f"User team set to: {row[0]['team_name']}"}
    finally:
        await db.close()


@router.get("/info", response_model=LeagueInfo)
async def get_league_info():
    db = await get_db()
    try:
        row = await db.execute_fetchall("SELECT * FROM league LIMIT 1")
        if not row:
            raise HTTPException(status_code=404, detail="League not synced yet. POST /api/v1/league/sync first.")
        r = row[0]
        return LeagueInfo(
            id=r["id"], espn_id=r["espn_id"], name=r["name"],
            season=r["season"], current_week=r["current_week"],
            num_teams=r["num_teams"], scoring_type=r["scoring_type"] or "PPR",
        )
    finally:
        await db.close()


@router.get("/teams")
async def get_teams():
    """Teams in standings order, shaped for the frontend (client.ts Team)."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT * FROM team ORDER BY wins DESC, points_for DESC")
        return [_team_payload(r, i + 1) for i, r in enumerate(rows)]
    finally:
        await db.close()


@router.get("/roster/{team_id}")
async def get_team_roster(team_id: int):
    db = await get_db()
    try:
        rows = await db.execute_fetchall("""
            SELECT p.*, re.slot, re.acquisition_type
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ?
            ORDER BY CASE re.slot
                WHEN 'QB' THEN 1 WHEN 'RB' THEN 2 WHEN 'WR' THEN 3
                WHEN 'TE' THEN 4 WHEN 'FLEX' THEN 5 WHEN 'K' THEN 6
                WHEN 'DST' THEN 7 WHEN 'BE' THEN 8 WHEN 'IR' THEN 9
            END
        """, (team_id,))
        return [
            {
                "player": {
                    "id": r["id"], "espn_id": r["espn_id"], "full_name": r["full_name"],
                    "position": r["position"], "nfl_team": r["nfl_team"],
                    "status": r["status"], "injury_status": r["injury_status"],
                    "projected_points": r["projected_points"],
                    "ros_projection": r["ros_projection"],
                    "composite_score": r["composite_score"],
                    "trade_value": r["trade_value"],
                    "boom_probability": r["boom_probability"],
                    "bust_probability": r["bust_probability"],
                    "sleeper_trending_add": r["sleeper_trending_add"],
                    "sleeper_trending_drop": r["sleeper_trending_drop"],
                    "headshot_url": r["headshot_url"],
                },
                "slot": r["slot"],
                "acquisition_type": r["acquisition_type"],
            }
            for r in rows
        ]
    finally:
        await db.close()


@router.get("/dashboard")
async def get_dashboard():
    """Dashboard summary, shaped for the frontend (client.ts Dashboard)."""
    db = await get_db()
    try:
        league_row = await db.execute_fetchall("SELECT * FROM league LIMIT 1")
        if not league_row:
            raise HTTPException(status_code=404, detail="League not synced yet")
        lr = league_row[0]

        team_row = await db.execute_fetchall("SELECT * FROM team WHERE is_user_team = 1 LIMIT 1")
        if not team_row:
            raise HTTPException(status_code=404, detail="User team not identified")
        tr = team_row[0]

        # Standing and points rank
        all_teams = await db.execute_fetchall(
            "SELECT id FROM team WHERE league_id = ? ORDER BY wins DESC, points_for DESC",
            (lr["id"],)
        )
        standing = next((i + 1 for i, t in enumerate(all_teams) if t["id"] == tr["id"]), 0)

        pts_teams = await db.execute_fetchall(
            "SELECT id FROM team WHERE league_id = ? ORDER BY points_for DESC",
            (lr["id"],)
        )
        points_rank = next((i + 1 for i, t in enumerate(pts_teams) if t["id"] == tr["id"]), 0)

        # Unread notifications as alerts
        notifs = await db.execute_fetchall(
            "SELECT * FROM notification WHERE is_read = 0 ORDER BY created_at DESC LIMIT 5"
        )
        alerts = [
            {"type": n["type"], "title": n["title"], "message": n["body"]}
            for n in notifs
        ]

        return {
            "teamSummary": _team_payload(tr, standing),
            "alerts": alerts,
            "quickStats": {
                "standing": standing,
                "pointsRank": points_rank,
                "record": f"{tr['wins']}-{tr['losses']}"
                          + (f"-{tr['ties']}" if tr["ties"] else ""),
            },
        }
    finally:
        await db.close()


@router.get("/power-rankings")
async def get_power_rankings():
    """Power rankings shaped for the frontend (client.ts PowerRanking).

    Falls back to standings order when the power-ranking job hasn't run.
    """
    db = await get_db()
    try:
        rows = await db.execute_fetchall("""
            SELECT * FROM team
            WHERE power_rank_score IS NOT NULL
            ORDER BY power_rank_score DESC
        """)
        if not rows:
            rows = await db.execute_fetchall(
                "SELECT * FROM team ORDER BY wins DESC, points_for DESC"
            )
        return [
            {
                "rank": i + 1,
                "teamId": str(r["id"]),
                "teamName": r["team_name"],
                "score": r["power_rank_score"] or r["points_for"] or 0,
                "trend": 0,
            }
            for i, r in enumerate(rows)
        ]
    finally:
        await db.close()
