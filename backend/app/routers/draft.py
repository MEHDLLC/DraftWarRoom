from fastapi import APIRouter, HTTPException
from ..database import get_db
from ..schemas.models import DraftPickInfo, PlayerInfo, TeamInfo

router = APIRouter()


@router.get("/picks", response_model=list[DraftPickInfo])
async def get_draft_picks():
    """Get all draft picks with player and team details."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """
            SELECT
                dp.round, dp.pick_number, dp.overall_pick, dp.adp,
                p.id AS player_id, p.espn_id, p.full_name, p.position,
                p.nfl_team, p.status, p.injury_status,
                p.projected_points, p.ros_projection, p.composite_score,
                p.trade_value, p.boom_probability, p.bust_probability,
                p.sleeper_trending_add, p.sleeper_trending_drop, p.headshot_url,
                t.id AS team_id, t.espn_team_id, t.team_name, t.owner_name,
                t.wins, t.losses, t.ties, t.points_for, t.points_against,
                t.is_user_team, t.power_rank_score, t.playoff_probability
            FROM draft_pick dp
            JOIN player p ON p.id = dp.player_id
            JOIN team t ON t.id = dp.team_id
            ORDER BY dp.overall_pick ASC
            """
        )

        if not rows:
            return []

        return [
            DraftPickInfo(
                round=r["round"],
                pick_number=r["pick_number"],
                overall_pick=r["overall_pick"],
                adp=r["adp"],
                value_diff=round(r["adp"] - r["overall_pick"], 1) if r["adp"] else None,
                player=PlayerInfo(
                    id=r["player_id"],
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
                ),
                team=TeamInfo(
                    id=r["team_id"],
                    espn_team_id=r["espn_team_id"],
                    team_name=r["team_name"],
                    owner_name=r["owner_name"],
                    wins=r["wins"],
                    losses=r["losses"],
                    ties=r["ties"],
                    points_for=r["points_for"],
                    points_against=r["points_against"],
                    is_user_team=bool(r["is_user_team"]),
                    power_rank_score=r["power_rank_score"],
                    playoff_probability=r["playoff_probability"],
                ),
            )
            for r in rows
        ]
    finally:
        await db.close()


@router.get("/value-tracker")
async def get_draft_value_tracker():
    """Analyze draft value: compare each pick's actual performance vs ADP."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """
            SELECT
                dp.round, dp.pick_number, dp.overall_pick, dp.adp,
                p.id AS player_id, p.full_name, p.position, p.nfl_team,
                p.composite_score, p.ros_projection,
                t.id AS team_id, t.team_name, t.is_user_team
            FROM draft_pick dp
            JOIN player p ON p.id = dp.player_id
            JOIN team t ON t.id = dp.team_id
            ORDER BY dp.overall_pick ASC
            """
        )

        if not rows:
            return {"picks": [], "summary": {"total_value": 0, "best_pick": None, "worst_pick": None}}

        picks = []
        best_pick = None
        worst_pick = None
        user_total_value = 0
        user_pick_count = 0

        for r in rows:
            value_diff = round(r["adp"] - r["overall_pick"], 1) if r["adp"] else 0
            # Positive value_diff = drafted later than ADP (good value)
            # Negative value_diff = drafted earlier than ADP (reach)

            # Also factor in actual performance via composite score
            performance_grade = "N/A"
            score = r["composite_score"] or 0
            if score >= 80:
                performance_grade = "Elite"
            elif score >= 60:
                performance_grade = "Strong"
            elif score >= 40:
                performance_grade = "Average"
            elif score >= 20:
                performance_grade = "Below Average"
            elif score > 0:
                performance_grade = "Bust"

            pick_data = {
                "round": r["round"],
                "pick_number": r["pick_number"],
                "overall_pick": r["overall_pick"],
                "player_name": r["full_name"],
                "player_id": r["player_id"],
                "position": r["position"],
                "nfl_team": r["nfl_team"],
                "team_name": r["team_name"],
                "is_user_team": bool(r["is_user_team"]),
                "adp": r["adp"],
                "value_diff": value_diff,
                "composite_score": score,
                "performance_grade": performance_grade,
            }
            picks.append(pick_data)

            if r["is_user_team"]:
                user_total_value += value_diff
                user_pick_count += 1

                if best_pick is None or value_diff > best_pick["value_diff"]:
                    best_pick = pick_data
                if worst_pick is None or value_diff < worst_pick["value_diff"]:
                    worst_pick = pick_data

        return {
            "picks": picks,
            "summary": {
                "total_value": round(user_total_value, 1),
                "avg_value_per_pick": (
                    round(user_total_value / user_pick_count, 1) if user_pick_count else 0
                ),
                "best_pick": best_pick,
                "worst_pick": worst_pick,
            },
        }
    finally:
        await db.close()
