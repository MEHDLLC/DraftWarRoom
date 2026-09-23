"""
Sync the NFL schedule and per-position points-allowed rankings into
nfl_team_schedule. This powers matchup grades, strength of schedule,
bye-week detection, and the matchup factor of the composite score.
"""
import asyncio

from ..database import get_db
from ..config import get_settings
from ..utils.constants import normalize_nfl_team, normalize_position

# Positions we compute points-allowed rankings for. K and DST are left NULL
# (nflverse weekly stats only cover offensive skill positions reliably).
_PA_POSITIONS = ("QB", "RB", "WR", "TE")


async def sync_nfl_schedule():
    """Populate nfl_team_schedule from nflverse games + weekly stats."""
    from ..adapters.nflverse_adapter import get_schedules, get_weekly_stats

    settings = get_settings()
    season = settings.nfl_season

    games = await asyncio.to_thread(get_schedules, season)
    if games is None or games.empty:
        print(f"Schedule sync: no games found for season {season}")
        return

    # Points allowed per position by each defense, from played weeks
    pa = await asyncio.to_thread(_points_allowed_by_defense, season)

    db = await get_db()
    try:
        rows_written = 0
        for _, game in games.iterrows():
            week = int(game["week"])
            home = normalize_nfl_team(str(game["home_team"]))
            away = normalize_nfl_team(str(game["away_team"]))

            for team, opponent, is_home in ((home, away, 1), (away, home, 0)):
                opp_pa = pa.get(opponent, {})
                await db.execute("""
                    INSERT INTO nfl_team_schedule
                        (nfl_team, week, opponent, is_home,
                         pa_qb_rank, pa_qb_ppg, pa_rb_rank, pa_rb_ppg,
                         pa_wr_rank, pa_wr_ppg, pa_te_rank, pa_te_ppg)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(nfl_team, week) DO UPDATE SET
                        opponent=excluded.opponent, is_home=excluded.is_home,
                        pa_qb_rank=excluded.pa_qb_rank, pa_qb_ppg=excluded.pa_qb_ppg,
                        pa_rb_rank=excluded.pa_rb_rank, pa_rb_ppg=excluded.pa_rb_ppg,
                        pa_wr_rank=excluded.pa_wr_rank, pa_wr_ppg=excluded.pa_wr_ppg,
                        pa_te_rank=excluded.pa_te_rank, pa_te_ppg=excluded.pa_te_ppg
                """, (
                    team, week, opponent, is_home,
                    *(v for pos in _PA_POSITIONS
                      for v in (opp_pa.get(pos, {}).get("rank"),
                                opp_pa.get(pos, {}).get("ppg"))),
                ))
                rows_written += 1
        await db.commit()
        print(f"Schedule sync: {rows_written} team-week rows for season {season}"
              f" ({'with' if pa else 'without'} points-allowed data)")
    finally:
        await db.close()


def _points_allowed_by_defense(season: int) -> dict[str, dict[str, dict]]:
    """Aggregate fantasy points allowed by each defense per position.

    Returns {defense_team: {position: {"ppg": float, "rank": int}}} where
    rank 1 = allows the most points (softest matchup). Falls back to the
    previous season when the current one has no data yet.
    """
    from ..adapters.nflverse_adapter import get_weekly_stats

    stats = get_weekly_stats(season)
    if stats is None or stats.empty:
        stats = get_weekly_stats(season - 1)
    if stats is None or stats.empty:
        return {}

    # Column names differ between nflverse schema versions
    team_col = "team" if "team" in stats.columns else "recent_team"
    points_col = "fantasy_points_ppr" if "fantasy_points_ppr" in stats.columns else "fantasy_points"
    if "opponent_team" not in stats.columns or points_col not in stats.columns:
        return {}

    totals: dict[str, dict[str, dict]] = {}
    for _, row in stats.iterrows():
        pos = normalize_position(str(row.get("position") or ""))
        if pos not in _PA_POSITIONS:
            continue
        defense = normalize_nfl_team(str(row.get("opponent_team") or ""))
        week = row.get("week")
        pts = row.get(points_col) or 0
        if not defense or defense == "NAN" or week is None:
            continue
        d = totals.setdefault(defense, {}).setdefault(pos, {"total": 0.0, "weeks": set()})
        d["total"] += float(pts)
        d["weeks"].add(int(week))

    result: dict[str, dict[str, dict]] = {}
    for pos in _PA_POSITIONS:
        ppg_by_team = []
        for team, positions in totals.items():
            d = positions.get(pos)
            if d and d["weeks"]:
                ppg_by_team.append((team, d["total"] / len(d["weeks"])))
        # Rank 1 = most points allowed = easiest matchup
        ppg_by_team.sort(key=lambda x: x[1], reverse=True)
        for rank, (team, ppg) in enumerate(ppg_by_team, start=1):
            result.setdefault(team, {})[pos] = {"ppg": round(ppg, 2), "rank": rank}
    return result
