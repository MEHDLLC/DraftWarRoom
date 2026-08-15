from fastapi import APIRouter, HTTPException
from ..database import get_db
from ..schemas.models import LineupAdvice, OptimalLineupResult

router = APIRouter()


@router.get("/advice", response_model=LineupAdvice)
async def get_lineup_recommendations():
    """Get lineup recommendations for the user's team for the current week."""
    db = await get_db()
    try:
        # Get current week from league
        league_rows = await db.execute_fetchall("SELECT current_week FROM league LIMIT 1")
        if not league_rows:
            raise HTTPException(status_code=404, detail="League not synced yet")
        current_week = league_rows[0]["current_week"]

        # Get user team
        team_rows = await db.execute_fetchall("SELECT id FROM team WHERE is_user_team = 1 LIMIT 1")
        if not team_rows:
            raise HTTPException(status_code=404, detail="User team not identified")
        team_id = team_rows[0]["id"]

        # Try the engine module first
        try:
            from ..engine.lineup_advisor import get_lineup_advice
            advice = await get_lineup_advice(db, team_id, current_week)
            return advice
        except ImportError:
            pass

        # Fallback: build advice from roster and composite scores
        rows = await db.execute_fetchall(
            """
            SELECT p.id, p.full_name, p.position, p.composite_score,
                   p.projected_points, p.boom_probability, p.bust_probability,
                   re.slot
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ?
            ORDER BY p.composite_score DESC
            """,
            (team_id,),
        )

        starters = []
        bench = []
        for r in rows:
            entry = {
                "player_id": r["id"],
                "player_name": r["full_name"],
                "position": r["position"],
                "recommended_slot": r["slot"],
                "composite_score": r["composite_score"] or 0,
                "explanation": f"Projected {r['projected_points'] or 0:.1f} pts",
                "boom_probability": r["boom_probability"] or 0,
                "bust_probability": r["bust_probability"] or 0,
            }
            if r["slot"] not in ("BE", "IR"):
                starters.append(entry)
            else:
                bench.append(entry)

        # Generate swap suggestions: bench players scoring higher than starters
        swap_suggestions = []
        for bench_player in bench:
            for starter in starters:
                if (
                    bench_player["position"] == starter["position"]
                    and bench_player["composite_score"] > starter["composite_score"]
                ):
                    swap_suggestions.append({
                        "bench_player": bench_player["player_name"],
                        "bench_score": bench_player["composite_score"],
                        "starter_player": starter["player_name"],
                        "starter_score": starter["composite_score"],
                        "reason": (
                            f"{bench_player['player_name']} "
                            f"({bench_player['composite_score']:.1f}) has a higher "
                            f"composite score than {starter['player_name']} "
                            f"({starter['composite_score']:.1f})"
                        ),
                    })

        return LineupAdvice(
            week=current_week,
            starters=starters,
            bench=bench,
            swap_suggestions=swap_suggestions,
        )
    finally:
        await db.close()


@router.get("/optimal/{week}", response_model=OptimalLineupResult)
async def get_optimal_lineup_comparison(week: int):
    """Get optimal lineup comparison for a past week."""
    db = await get_db()
    try:
        # Get user team
        team_rows = await db.execute_fetchall("SELECT id FROM team WHERE is_user_team = 1 LIMIT 1")
        if not team_rows:
            raise HTTPException(status_code=404, detail="User team not identified")
        team_id = team_rows[0]["id"]

        # Try engine module
        try:
            from ..engine.optimal_lineup import get_optimal_lineup
            result = await get_optimal_lineup(db, team_id, week)
            return result
        except ImportError:
            pass

        # Fallback: check pre-computed optimal lineup table
        rows = await db.execute_fetchall(
            """
            SELECT actual_points, optimal_points, points_left_on_bench, optimal_roster
            FROM optimal_lineup
            WHERE team_id = ? AND week = ?
            """,
            (team_id, week),
        )
        if rows:
            import json
            r = rows[0]
            return OptimalLineupResult(
                week=week,
                actual_points=r["actual_points"] or 0,
                optimal_points=r["optimal_points"] or 0,
                points_left_on_bench=r["points_left_on_bench"] or 0,
                optimal_roster=json.loads(r["optimal_roster"]) if r["optimal_roster"] else [],
            )

        raise HTTPException(
            status_code=404,
            detail=f"Optimal lineup data not available for week {week}. "
                   "Data is computed after each week completes.",
        )
    finally:
        await db.close()
