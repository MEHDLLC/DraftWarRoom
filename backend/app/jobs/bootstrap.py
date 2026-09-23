"""
Startup bootstrap: backfill missing or stale data in the background so the
app gives correct advice right after a deploy or restart, instead of waiting
for the next cron window. Each step is gated on a staleness check so a
crash-looping container doesn't hammer external APIs.
"""
import asyncio

from ..database import get_db

# Per-step ceiling so one hung upstream call can't stall the whole chain
_STEP_TIMEOUT_S = 300


async def _run_step(name: str, coro) -> None:
    print(f"Bootstrap: starting {name}")
    try:
        await asyncio.wait_for(coro, timeout=_STEP_TIMEOUT_S)
    except asyncio.TimeoutError:
        print(f"Bootstrap {name} timed out after {_STEP_TIMEOUT_S}s")
    except Exception as e:
        print(f"Bootstrap {name} failed: {e}")


async def bootstrap_data():
    """Run gated data syncs. Intended to run as a background task on startup."""
    from .sync_league import sync_league_data
    from .sync_schedule import sync_nfl_schedule
    from .sync_players import sync_sleeper_data, sync_nflverse_stats, update_composite_scores

    needs = await _check_needs()
    print(f"Bootstrap needs: {needs}")

    if needs["league"]:
        await _run_step("league sync", sync_league_data())
    if needs["schedule"]:
        await _run_step("schedule sync", sync_nfl_schedule())
    if needs["sleeper"]:
        await _run_step("sleeper sync", sync_sleeper_data())
    if needs["stats"]:
        await _run_step("nflverse sync", sync_nflverse_stats())
    if any(needs.values()):
        await _run_step("composite scores", update_composite_scores())

    print(f"Bootstrap complete (ran: {[k for k, v in needs.items() if v] or 'nothing'})")

    from .report import print_team_report
    await _run_step("team report", print_team_report())


async def _check_needs() -> dict[str, bool]:
    """Decide which syncs are worth running at startup."""
    needs = {"league": False, "schedule": False, "sleeper": False, "stats": False}
    db = await get_db()
    try:
        # League data missing, or last synced over an hour ago
        rows = await db.execute_fetchall("""
            SELECT (julianday('now') - julianday(updated_at)) * 24 AS hours_old
            FROM league LIMIT 1
        """)
        hours_old = rows[0]["hours_old"] if rows else None
        needs["league"] = hours_old is None or hours_old > 1

        rows = await db.execute_fetchall("SELECT COUNT(*) AS c FROM nfl_team_schedule")
        needs["schedule"] = rows[0]["c"] == 0

        rows = await db.execute_fetchall(
            "SELECT COUNT(*) AS c FROM player WHERE sleeper_trending_add > 0"
        )
        needs["sleeper"] = rows[0]["c"] == 0

        rows = await db.execute_fetchall("SELECT COUNT(*) AS c FROM player_weekly_stat")
        needs["stats"] = rows[0]["c"] == 0

        # Everything is stale after half a day (e.g. the scheduler was down):
        # refresh it all, not just the league
        if hours_old is None or hours_old > 12:
            needs = {k: True for k in needs}
    except Exception as e:
        print(f"Bootstrap check failed: {e}")
    finally:
        await db.close()
    return needs
