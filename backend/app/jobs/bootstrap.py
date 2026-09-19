"""
Startup bootstrap: backfill missing or stale data in the background so the
app gives correct advice right after a deploy or restart, instead of waiting
for the next cron window. Each step is gated on a staleness check so a
crash-looping container doesn't hammer external APIs.
"""
from ..database import get_db


async def bootstrap_data():
    """Run gated data syncs. Intended to run as a background task on startup."""
    from .sync_league import sync_league_data
    from .sync_schedule import sync_nfl_schedule
    from .sync_players import sync_sleeper_data, sync_nflverse_stats, update_composite_scores

    needs = await _check_needs()

    if needs["league"]:
        try:
            await sync_league_data()
        except Exception as e:
            print(f"Bootstrap league sync failed: {e}")

    if needs["schedule"]:
        try:
            await sync_nfl_schedule()
        except Exception as e:
            print(f"Bootstrap schedule sync failed: {e}")

    if needs["sleeper"]:
        try:
            await sync_sleeper_data()
        except Exception as e:
            print(f"Bootstrap sleeper sync failed: {e}")

    if needs["stats"]:
        try:
            await sync_nflverse_stats()
        except Exception as e:
            print(f"Bootstrap nflverse sync failed: {e}")

    if any(needs.values()):
        try:
            await update_composite_scores()
        except Exception as e:
            print(f"Bootstrap composite score update failed: {e}")

    print(f"Bootstrap complete (ran: {[k for k, v in needs.items() if v] or 'nothing'})")


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
        needs["league"] = not rows or rows[0]["hours_old"] is None or rows[0]["hours_old"] > 1

        rows = await db.execute_fetchall("SELECT COUNT(*) AS c FROM nfl_team_schedule")
        needs["schedule"] = rows[0]["c"] == 0

        rows = await db.execute_fetchall(
            "SELECT COUNT(*) AS c FROM player WHERE sleeper_trending_add > 0"
        )
        needs["sleeper"] = rows[0]["c"] == 0

        rows = await db.execute_fetchall("SELECT COUNT(*) AS c FROM player_weekly_stat")
        needs["stats"] = rows[0]["c"] == 0
    except Exception as e:
        print(f"Bootstrap check failed: {e}")
    finally:
        await db.close()
    return needs
