"""Additional sync-related endpoints for manual control."""
from fastapi import APIRouter, HTTPException
from ..jobs.sync_players import sync_sleeper_data, sync_nflverse_stats, update_composite_scores
from ..engine.power_rankings import calculate_power_rankings
from ..engine.playoff_simulator import simulate_playoffs

router = APIRouter()


@router.post("/sleeper")
async def trigger_sleeper_sync():
    """Manually trigger Sleeper data sync."""
    try:
        await sync_sleeper_data()
        return {"status": "ok", "message": "Sleeper sync completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nflverse")
async def trigger_nflverse_sync():
    """Manually trigger nflverse stats sync."""
    try:
        await sync_nflverse_stats()
        return {"status": "ok", "message": "nflverse sync completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scores")
async def trigger_score_update():
    """Manually trigger composite score recalculation."""
    try:
        await update_composite_scores()
        return {"status": "ok", "message": "Composite scores updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/power-rankings")
async def trigger_power_rankings():
    """Manually trigger power rankings calculation."""
    try:
        rankings = await calculate_power_rankings()
        return {"status": "ok", "rankings": rankings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playoff-odds")
async def trigger_playoff_simulation():
    """Manually trigger playoff probability simulation."""
    try:
        results = await simulate_playoffs()
        return {"status": "ok", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
