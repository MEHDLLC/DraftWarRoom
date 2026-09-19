"""
APScheduler configuration for background jobs.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio

scheduler = AsyncIOScheduler()


def _run_async(coro_func):
    """Wrapper to run async functions from sync scheduler callbacks."""
    async def wrapper():
        await coro_func()
    def sync_wrapper():
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(wrapper())
        else:
            loop.run_until_complete(wrapper())
    return sync_wrapper


def start_scheduler():
    """Start the background job scheduler.

    Note: cron hours below are in the server's local time, which is UTC in
    the Docker/Railway deployment. ET kickoffs: Sun 1:00 PM ET = 17:00 UTC,
    Thu 8:15 PM ET = 00:15 UTC Friday.
    """
    from .sync_league import sync_league_data
    from .sync_players import sync_sleeper_data, sync_nflverse_stats, update_composite_scores
    from .sync_schedule import sync_nfl_schedule
    from .notifications import check_lineup_guardrails, generate_weekly_recap, check_waiver_opportunities

    # League sync every 6 hours
    scheduler.add_job(
        _run_async(sync_league_data),
        CronTrigger(hour="*/6"),
        id="league_sync",
        replace_existing=True,
    )

    # Sleeper trending data every 4 hours
    scheduler.add_job(
        _run_async(sync_sleeper_data),
        CronTrigger(hour="*/4"),
        id="sleeper_sync",
        replace_existing=True,
    )

    # nflverse stats daily at 5 AM
    scheduler.add_job(
        _run_async(sync_nflverse_stats),
        CronTrigger(hour=5),
        id="nflverse_sync",
        replace_existing=True,
    )

    # NFL schedule + points-allowed rankings daily at 5:30 AM
    scheduler.add_job(
        _run_async(sync_nfl_schedule),
        CronTrigger(hour=5, minute=30),
        id="nfl_schedule_sync",
        replace_existing=True,
    )

    # Composite score recalculation after syncs
    scheduler.add_job(
        _run_async(update_composite_scores),
        CronTrigger(hour="1,7,13,19"),
        id="composite_scores",
        replace_existing=True,
    )

    # Sunday hourly updates during game windows
    scheduler.add_job(
        _run_async(sync_league_data),
        CronTrigger(day_of_week="sun", hour="10-23"),
        id="sunday_sync",
        replace_existing=True,
    )

    # Lineup guardrails - Thursday and Sunday morning
    scheduler.add_job(
        _run_async(check_lineup_guardrails),
        CronTrigger(day_of_week="thu", hour=10),
        id="thursday_lineup_check",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_async(check_lineup_guardrails),
        CronTrigger(day_of_week="sun", hour=9),
        id="sunday_lineup_check",
        replace_existing=True,
    )

    # Pre-kickoff guardrails: fresh sync then check ~90 min before kickoff.
    # Sunday 1 PM ET slate: sync 15:00 UTC, check 15:30 UTC.
    scheduler.add_job(
        _run_async(sync_league_data),
        CronTrigger(day_of_week="sun", hour=15, minute=0),
        id="sunday_pregame_sync",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_async(check_lineup_guardrails),
        CronTrigger(day_of_week="sun", hour=15, minute=30),
        id="sunday_pregame_check",
        replace_existing=True,
    )
    # Thursday Night Football (8:15 PM ET = 00:15 UTC): sync 22:15, check 22:45 UTC.
    scheduler.add_job(
        _run_async(sync_league_data),
        CronTrigger(day_of_week="thu", hour=22, minute=15),
        id="thursday_pregame_sync",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_async(check_lineup_guardrails),
        CronTrigger(day_of_week="thu", hour=22, minute=45),
        id="thursday_pregame_check",
        replace_existing=True,
    )

    # Monday morning recap
    scheduler.add_job(
        _run_async(generate_weekly_recap),
        CronTrigger(day_of_week="mon", hour=8),
        id="monday_recap",
        replace_existing=True,
    )

    # Tuesday waiver wire tips
    scheduler.add_job(
        _run_async(check_waiver_opportunities),
        CronTrigger(day_of_week="tue", hour=6),
        id="tuesday_waivers",
        replace_existing=True,
    )

    scheduler.start()
    print("Scheduler started with background jobs")


def shutdown_scheduler():
    """Shut down the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler shut down")
