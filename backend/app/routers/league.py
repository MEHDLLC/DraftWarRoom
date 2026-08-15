from fastapi import APIRouter, HTTPException
from ..database import get_db
from ..schemas.models import LeagueInfo, TeamInfo, DashboardStats, PowerRanking
from ..jobs.sync_league import sync_league_data

router = APIRouter()


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


@router.get("/teams", response_model=list[TeamInfo])
async def get_teams():
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT * FROM team ORDER BY wins DESC, points_for DESC")
        return [
            TeamInfo(
                id=r["id"], espn_team_id=r["espn_team_id"], team_name=r["team_name"],
                owner_name=r["owner_name"], wins=r["wins"], losses=r["losses"],
                ties=r["ties"], points_for=r["points_for"], points_against=r["points_against"],
                is_user_team=bool(r["is_user_team"]),
                power_rank_score=r["power_rank_score"],
                playoff_probability=r["playoff_probability"],
            )
            for r in rows
        ]
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


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard():
    db = await get_db()
    try:
        league_row = await db.execute_fetchall("SELECT * FROM league LIMIT 1")
        if not league_row:
            raise HTTPException(status_code=404, detail="League not synced yet")
        lr = league_row[0]
        league = LeagueInfo(
            id=lr["id"], espn_id=lr["espn_id"], name=lr["name"],
            season=lr["season"], current_week=lr["current_week"],
            num_teams=lr["num_teams"], scoring_type=lr["scoring_type"] or "PPR",
        )

        # User team
        team_row = await db.execute_fetchall("SELECT * FROM team WHERE is_user_team = 1 LIMIT 1")
        if not team_row:
            raise HTTPException(status_code=404, detail="User team not identified")
        tr = team_row[0]
        user_team = TeamInfo(
            id=tr["id"], espn_team_id=tr["espn_team_id"], team_name=tr["team_name"],
            owner_name=tr["owner_name"], wins=tr["wins"], losses=tr["losses"],
            ties=tr["ties"], points_for=tr["points_for"], points_against=tr["points_against"],
            is_user_team=True, power_rank_score=tr["power_rank_score"],
            playoff_probability=tr["playoff_probability"],
        )

        # Standing
        all_teams = await db.execute_fetchall(
            "SELECT id FROM team WHERE league_id = ? ORDER BY wins DESC, points_for DESC",
            (lr["id"],)
        )
        standing = next((i + 1 for i, t in enumerate(all_teams) if t["id"] == tr["id"]), 0)

        # Points rank
        pts_teams = await db.execute_fetchall(
            "SELECT id FROM team WHERE league_id = ? ORDER BY points_for DESC",
            (lr["id"],)
        )
        points_rank = next((i + 1 for i, t in enumerate(pts_teams) if t["id"] == tr["id"]), 0)

        # Recent matchup results
        recent = await db.execute_fetchall("""
            SELECT CASE
                WHEN winner_team_id = ? THEN 'W'
                WHEN winner_team_id IS NULL THEN '-'
                ELSE 'L'
            END as result
            FROM matchup
            WHERE (home_team_id = ? OR away_team_id = ?) AND winner_team_id IS NOT NULL
            ORDER BY week DESC LIMIT 5
        """, (tr["id"], tr["id"], tr["id"]))
        recent_trend = [r["result"] for r in reversed(recent)]

        # Unread notifications
        notifs = await db.execute_fetchall(
            "SELECT * FROM notification WHERE is_read = 0 ORDER BY created_at DESC LIMIT 5"
        )
        alerts = [
            {
                "id": n["id"], "title": n["title"], "body": n["body"],
                "type": n["type"], "priority": n["priority"],
                "is_read": False, "created_at": n["created_at"],
            }
            for n in notifs
        ]

        return DashboardStats(
            league=league, user_team=user_team,
            record=f"{tr['wins']}-{tr['losses']}" + (f"-{tr['ties']}" if tr["ties"] else ""),
            standing=standing, points_rank=points_rank,
            recent_trend=recent_trend, alerts=alerts,
        )
    finally:
        await db.close()


@router.get("/power-rankings", response_model=list[PowerRanking])
async def get_power_rankings():
    db = await get_db()
    try:
        rows = await db.execute_fetchall("""
            SELECT * FROM team
            WHERE power_rank_score IS NOT NULL
            ORDER BY power_rank_score DESC
        """)
        return [
            PowerRanking(
                rank=i + 1,
                team=TeamInfo(
                    id=r["id"], espn_team_id=r["espn_team_id"], team_name=r["team_name"],
                    owner_name=r["owner_name"], wins=r["wins"], losses=r["losses"],
                    ties=r["ties"], points_for=r["points_for"], points_against=r["points_against"],
                    is_user_team=bool(r["is_user_team"]),
                    power_rank_score=r["power_rank_score"],
                    playoff_probability=r["playoff_probability"],
                ),
                score=r["power_rank_score"],
            )
            for i, r in enumerate(rows)
        ]
    finally:
        await db.close()
