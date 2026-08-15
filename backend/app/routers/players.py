from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..database import get_db
from ..schemas.models import PlayerInfo, PlayerWeeklyStat

router = APIRouter()


@router.get("/", response_model=list[PlayerInfo])
async def list_players(
    position: Optional[str] = Query(None, description="Filter by position (QB, RB, WR, TE, K, DST)"),
    search: Optional[str] = Query(None, description="Search by player name"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List all players with optional position filter and search query."""
    db = await get_db()
    try:
        conditions = []
        params: list = []

        if position:
            conditions.append("position = ?")
            params.append(position.upper())

        if search:
            conditions.append("full_name LIKE ?")
            params.append(f"%{search}%")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT * FROM player
            {where_clause}
            ORDER BY composite_score DESC, projected_points DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        rows = await db.execute_fetchall(query, tuple(params))
        return [
            PlayerInfo(
                id=r["id"],
                espn_id=r["espn_id"],
                full_name=r["full_name"],
                position=r["position"],
                nfl_team=r["nfl_team"],
                status=r["status"],
                injury_status=r["injury_status"],
                projected_points=r["projected_points"] or 0,
                ros_projection=r["ros_projection"] or 0,
                composite_score=r["composite_score"] or 0,
                trade_value=r["trade_value"] or 0,
                boom_probability=r["boom_probability"] or 0,
                bust_probability=r["bust_probability"] or 0,
                sleeper_trending_add=r["sleeper_trending_add"] or 0,
                sleeper_trending_drop=r["sleeper_trending_drop"] or 0,
                headshot_url=r["headshot_url"],
            )
            for r in rows
        ]
    finally:
        await db.close()


@router.get("/{player_id}", response_model=PlayerInfo)
async def get_player(player_id: int):
    """Get a single player's details."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT * FROM player WHERE id = ?", (player_id,)
        )
        if not rows:
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
        r = rows[0]
        return PlayerInfo(
            id=r["id"],
            espn_id=r["espn_id"],
            full_name=r["full_name"],
            position=r["position"],
            nfl_team=r["nfl_team"],
            status=r["status"],
            injury_status=r["injury_status"],
            projected_points=r["projected_points"] or 0,
            ros_projection=r["ros_projection"] or 0,
            composite_score=r["composite_score"] or 0,
            trade_value=r["trade_value"] or 0,
            boom_probability=r["boom_probability"] or 0,
            bust_probability=r["bust_probability"] or 0,
            sleeper_trending_add=r["sleeper_trending_add"] or 0,
            sleeper_trending_drop=r["sleeper_trending_drop"] or 0,
            headshot_url=r["headshot_url"],
        )
    finally:
        await db.close()


@router.get("/{player_id}/stats", response_model=list[PlayerWeeklyStat])
async def get_player_stats(player_id: int):
    """Get weekly stats for a player."""
    db = await get_db()
    try:
        # Verify player exists
        player_rows = await db.execute_fetchall(
            "SELECT id FROM player WHERE id = ?", (player_id,)
        )
        if not player_rows:
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")

        rows = await db.execute_fetchall(
            """
            SELECT week, fantasy_points, projected_points, snap_count,
                   snap_pct, targets, target_share, carries,
                   red_zone_targets, red_zone_carries
            FROM player_weekly_stat
            WHERE player_id = ?
            ORDER BY week ASC
            """,
            (player_id,),
        )
        return [
            PlayerWeeklyStat(
                week=r["week"],
                fantasy_points=r["fantasy_points"] or 0,
                projected_points=r["projected_points"] or 0,
                snap_count=r["snap_count"] or 0,
                snap_pct=r["snap_pct"] or 0,
                targets=r["targets"] or 0,
                target_share=r["target_share"] or 0,
                carries=r["carries"] or 0,
                red_zone_targets=r["red_zone_targets"] or 0,
                red_zone_carries=r["red_zone_carries"] or 0,
            )
            for r in rows
        ]
    finally:
        await db.close()
