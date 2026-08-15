from fastapi import APIRouter, HTTPException, Query
from ..database import get_db
from ..schemas.models import PlayerInfo, WaiverRecommendation

router = APIRouter()


@router.get("/recommendations", response_model=list[WaiverRecommendation])
async def get_waiver_recommendations_endpoint(
    limit: int = Query(15, ge=1, le=50),
):
    """Get waiver wire recommendations based on composite scores and availability."""
    db = await get_db()
    try:
        # Get user team for drop suggestions
        team_rows = await db.execute_fetchall("SELECT id FROM team WHERE is_user_team = 1 LIMIT 1")
        if not team_rows:
            raise HTTPException(status_code=404, detail="User team not identified")
        team_id = team_rows[0]["id"]

        # Try engine module
        try:
            from ..engine.waiver_advisor import get_waiver_recommendations
            recs = await get_waiver_recommendations(db, team_id, limit)
            return recs
        except ImportError:
            pass

        # Fallback: find top available players not on any roster
        available = await db.execute_fetchall(
            """
            SELECT p.*
            FROM player p
            LEFT JOIN roster_entry re ON re.player_id = p.id
            WHERE re.id IS NULL
              AND p.position IN ('QB', 'RB', 'WR', 'TE', 'K', 'DST')
              AND p.projected_points > 0
            ORDER BY p.composite_score DESC, p.projected_points DESC
            LIMIT ?
            """,
            (limit,),
        )

        # Get user's weakest bench players for drop suggestions
        bench_players = await db.execute_fetchall(
            """
            SELECT p.*
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ? AND re.slot = 'BE'
            ORDER BY p.composite_score ASC
            """,
            (team_id,),
        )

        results = []
        for r in available:
            player = PlayerInfo(
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

            # Find lowest-value bench player at same position as drop suggestion
            suggested_drop = None
            drop_explanation = None
            for bp in bench_players:
                if bp["position"] == r["position"]:
                    if (bp["composite_score"] or 0) < (r["composite_score"] or 0):
                        suggested_drop = PlayerInfo(
                            id=bp["id"],
                            espn_id=bp["espn_id"],
                            full_name=bp["full_name"],
                            position=bp["position"],
                            nfl_team=bp["nfl_team"],
                            status=bp["status"],
                            injury_status=bp["injury_status"],
                            projected_points=bp["projected_points"] or 0,
                            ros_projection=bp["ros_projection"] or 0,
                            composite_score=bp["composite_score"] or 0,
                            trade_value=bp["trade_value"] or 0,
                            boom_probability=bp["boom_probability"] or 0,
                            bust_probability=bp["bust_probability"] or 0,
                            sleeper_trending_add=bp["sleeper_trending_add"] or 0,
                            sleeper_trending_drop=bp["sleeper_trending_drop"] or 0,
                            headshot_url=bp["headshot_url"],
                        )
                        drop_explanation = (
                            f"{bp['full_name']} has a lower composite score "
                            f"({bp['composite_score'] or 0:.1f} vs {r['composite_score'] or 0:.1f})"
                        )
                        break

            trending_note = ""
            if r["sleeper_trending_add"] and r["sleeper_trending_add"] > 100:
                trending_note = f" Trending up on Sleeper (+{r['sleeper_trending_add']} adds)."

            results.append(
                WaiverRecommendation(
                    player=player,
                    composite_score=r["composite_score"] or 0,
                    explanation=(
                        f"{r['full_name']} ({r['position']}, {r['nfl_team'] or 'FA'}) "
                        f"projects {r['projected_points'] or 0:.1f} pts this week "
                        f"with a ROS projection of {r['ros_projection'] or 0:.1f}.{trending_note}"
                    ),
                    suggested_drop=suggested_drop,
                    drop_explanation=drop_explanation,
                )
            )

        return results
    finally:
        await db.close()


@router.get("/trending")
async def get_trending_players(
    limit: int = Query(20, ge=1, le=50),
):
    """Get trending players based on Sleeper add/drop data."""
    db = await get_db()
    try:
        # Top trending adds
        trending_adds = await db.execute_fetchall(
            """
            SELECT p.id, p.full_name, p.position, p.nfl_team,
                   p.projected_points, p.composite_score,
                   p.sleeper_trending_add, p.sleeper_trending_drop,
                   CASE WHEN re.id IS NOT NULL THEN 1 ELSE 0 END as is_rostered
            FROM player p
            LEFT JOIN roster_entry re ON re.player_id = p.id
            WHERE p.sleeper_trending_add > 0
            ORDER BY p.sleeper_trending_add DESC
            LIMIT ?
            """,
            (limit,),
        )

        # Top trending drops
        trending_drops = await db.execute_fetchall(
            """
            SELECT p.id, p.full_name, p.position, p.nfl_team,
                   p.projected_points, p.composite_score,
                   p.sleeper_trending_add, p.sleeper_trending_drop,
                   CASE WHEN re.id IS NOT NULL THEN 1 ELSE 0 END as is_rostered
            FROM player p
            LEFT JOIN roster_entry re ON re.player_id = p.id
            WHERE p.sleeper_trending_drop > 0
            ORDER BY p.sleeper_trending_drop DESC
            LIMIT ?
            """,
            (limit,),
        )

        def _format_trending(rows):
            return [
                {
                    "id": r["id"],
                    "full_name": r["full_name"],
                    "position": r["position"],
                    "nfl_team": r["nfl_team"],
                    "projected_points": r["projected_points"] or 0,
                    "composite_score": r["composite_score"] or 0,
                    "trending_add": r["sleeper_trending_add"] or 0,
                    "trending_drop": r["sleeper_trending_drop"] or 0,
                    "is_rostered": bool(r["is_rostered"]),
                }
                for r in rows
            ]

        return {
            "trending_adds": _format_trending(trending_adds),
            "trending_drops": _format_trending(trending_drops),
        }
    finally:
        await db.close()
