"""
Sync player data from Sleeper and nflverse to enrich local database.
"""
import asyncio

from ..database import get_db
from ..config import get_settings
from ..engine.scorer import compute_composite_score, injury_to_score, usage_trend_score, generate_explanation
from ..engine.boom_bust import calculate_boom_bust
from ..utils.constants import normalize_nfl_team, normalize_injury_status


async def sync_sleeper_data():
    """Sync trending data and injuries from Sleeper."""
    from ..adapters.sleeper_adapter import get_trending_players, get_all_players

    db = await get_db()
    try:
        # Adapter calls are synchronous httpx requests — run off the event loop
        trending_adds = await asyncio.to_thread(get_trending_players, "nfl", "add", 50)
        trending_drops = await asyncio.to_thread(get_trending_players, "nfl", "drop", 50)

        # Get full Sleeper player database for cross-referencing
        all_sleeper = await asyncio.to_thread(get_all_players)

        # Map Sleeper IDs to our players by name+team
        for trend in trending_adds:
            sleeper_id = trend["player_id"]
            if sleeper_id in all_sleeper:
                sp = all_sleeper[sleeper_id]
                name = f"{sp.get('first_name', '')} {sp.get('last_name', '')}".strip()
                team = normalize_nfl_team(sp.get("team"))
                if name and team:
                    await db.execute("""
                        UPDATE player SET sleeper_id = ?, sleeper_trending_add = ?,
                                          injury_status = COALESCE(?, injury_status)
                        WHERE full_name = ? AND nfl_team = ?
                    """, (sleeper_id, trend["count"],
                          normalize_injury_status(sp.get("injury_status")), name, team))

        for trend in trending_drops:
            sleeper_id = trend["player_id"]
            if sleeper_id in all_sleeper:
                sp = all_sleeper[sleeper_id]
                name = f"{sp.get('first_name', '')} {sp.get('last_name', '')}".strip()
                team = normalize_nfl_team(sp.get("team"))
                if name and team:
                    await db.execute("""
                        UPDATE player SET sleeper_trending_drop = ?
                        WHERE full_name = ? AND nfl_team = ?
                    """, (trend["count"], name, team))

        await db.commit()
        print(f"Sleeper sync: {len(trending_adds)} trending adds, {len(trending_drops)} drops")
    except Exception as e:
        print(f"Sleeper sync error: {e}")
    finally:
        await db.close()


async def sync_nflverse_stats():
    """Sync weekly stats and snap counts from nflverse."""
    from ..adapters.nflverse_adapter import get_weekly_stats, get_snap_counts

    settings = get_settings()
    season = settings.nfl_season
    db = await get_db()

    try:
        # Weekly stats (blocking download — run off the event loop). Early in
        # the season the current file can be empty; fall back to last season
        # so usage trends aren't all zero.
        stats_df = await asyncio.to_thread(get_weekly_stats, season)
        stats_season = season
        if stats_df is None or stats_df.empty:
            stats_df = await asyncio.to_thread(get_weekly_stats, season - 1)
            stats_season = season - 1

        if stats_df is not None and not stats_df.empty:
            # Column names differ between nflverse schema versions
            cols = stats_df.columns
            team_col = "team" if "team" in cols else "recent_team"
            int_col = "passing_interceptions" if "passing_interceptions" in cols else "interceptions"

            for _, row in stats_df.iterrows():
                # Find player by name and team
                name = row.get("player_display_name") or row.get("player_name", "")
                team = normalize_nfl_team(row.get(team_col, ""))
                week = int(row.get("week", 0))

                if not name or not week:
                    continue

                cursor = await db.execute(
                    "SELECT id FROM player WHERE full_name = ? AND nfl_team = ?",
                    (name, team)
                )
                player_row = await cursor.fetchone()
                if not player_row:
                    continue

                await db.execute("""
                    INSERT INTO player_weekly_stat
                    (player_id, season, week, fantasy_points, pass_yards, pass_tds,
                     interceptions, rush_yards, rush_tds, carries, receptions,
                     rec_yards, rec_tds, targets)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(player_id, season, week) DO UPDATE SET
                        fantasy_points=excluded.fantasy_points,
                        pass_yards=excluded.pass_yards, pass_tds=excluded.pass_tds,
                        interceptions=excluded.interceptions,
                        rush_yards=excluded.rush_yards, rush_tds=excluded.rush_tds,
                        carries=excluded.carries, receptions=excluded.receptions,
                        rec_yards=excluded.rec_yards, rec_tds=excluded.rec_tds,
                        targets=excluded.targets
                """, (
                    player_row["id"], stats_season, week,
                    row.get("fantasy_points_ppr", 0),
                    row.get("passing_yards", 0), row.get("passing_tds", 0),
                    row.get(int_col, 0),
                    row.get("rushing_yards", 0), row.get("rushing_tds", 0),
                    row.get("carries", 0), row.get("receptions", 0),
                    row.get("receiving_yards", 0), row.get("receiving_tds", 0),
                    row.get("targets", 0),
                ))
            await db.commit()

        # Snap counts
        snaps_df = await asyncio.to_thread(get_snap_counts, stats_season)
        if snaps_df is not None and not snaps_df.empty:
            for _, row in snaps_df.iterrows():
                name = row.get("player", "")
                team = normalize_nfl_team(row.get("team", ""))
                week = int(row.get("week", 0))

                if not name or not week:
                    continue

                cursor = await db.execute(
                    "SELECT id FROM player WHERE full_name = ? AND nfl_team = ?",
                    (name, team)
                )
                player_row = await cursor.fetchone()
                if not player_row:
                    continue

                await db.execute("""
                    UPDATE player_weekly_stat
                    SET snap_count = ?, snap_pct = ?
                    WHERE player_id = ? AND season = ? AND week = ?
                """, (
                    row.get("offense_snaps", 0),
                    row.get("offense_pct", 0),
                    player_row["id"], stats_season, week,
                ))
            await db.commit()

        print(f"nflverse stats sync complete (season {stats_season})")
    except Exception as e:
        print(f"nflverse sync error: {e}")
    finally:
        await db.close()


async def update_composite_scores():
    """Recalculate composite scores for all rostered players."""
    db = await get_db()
    try:
        settings = get_settings()
        season = settings.nfl_season

        # Current fantasy week (for matchup lookups)
        league_row = await db.execute_fetchall("SELECT current_week FROM league LIMIT 1")
        current_week = league_row[0]["current_week"] if league_row else 1

        # Opponent points-allowed for this week, keyed by NFL team.
        # A team with schedule data but no game this week is on bye.
        week_schedule = await db.execute_fetchall("""
            SELECT nfl_team, pa_qb_rank, pa_rb_rank, pa_wr_rank, pa_te_rank
            FROM nfl_team_schedule WHERE week = ?
        """, (current_week,))
        matchup_by_team = {r["nfl_team"]: dict(r) for r in week_schedule}
        have_schedule = bool(matchup_by_team)
        pa_col = {"QB": "pa_qb_rank", "RB": "pa_rb_rank", "WR": "pa_wr_rank", "TE": "pa_te_rank"}

        # Get all players with roster entries
        players = await db.execute_fetchall("""
            SELECT p.* FROM player p
            WHERE p.position IN ('QB', 'RB', 'WR', 'TE', 'K', 'DST')
        """)

        if not players:
            return

        # Weekly stats can be from last season early in the year — use
        # whichever season actually has rows.
        stats_season_row = await db.execute_fetchall(
            "SELECT MAX(season) as s FROM player_weekly_stat"
        )
        stats_season = (stats_season_row[0]["s"] if stats_season_row else None) or season

        # Collect all values for percentile calculations
        all_ros = []
        all_usage = []
        all_matchup = []
        all_community = []

        player_data = []
        for p in players:
            p = dict(p)

            # Get weekly stats for boom/bust and usage trend
            stats = await db.execute_fetchall("""
                SELECT fantasy_points, snap_pct FROM player_weekly_stat
                WHERE player_id = ? AND season = ? ORDER BY week
            """, (p["id"], stats_season))

            weekly_points = [s["fantasy_points"] for s in stats if s["fantasy_points"]]
            weekly_snaps = [s["snap_pct"] for s in stats if s["snap_pct"]]

            ros = p.get("ros_projection") or p.get("projected_points") or 0
            usage = usage_trend_score(weekly_snaps)
            injury = injury_to_score(p.get("injury_status"))
            community = (p.get("sleeper_trending_add") or 0)

            # Matchup: opponent's points-allowed rank at this position
            # (rank 1 = allows the most = softest matchup), scaled to 0-100
            # so it's comparable across positions. Neutral 50 with no
            # schedule/PA data; 0 when the player's team is on bye.
            matchup = 50.0
            team = p.get("nfl_team")
            if have_schedule and team:
                game = matchup_by_team.get(team)
                if game is None:
                    matchup = 0.0  # on bye
                else:
                    rank = game.get(pa_col.get(p["position"], ""), None)
                    if rank:
                        matchup = round((33 - rank) / 32 * 100, 1)

            boom, bust = calculate_boom_bust(weekly_points)

            all_ros.append(ros)
            all_usage.append(usage)
            all_matchup.append(matchup)
            all_community.append(community)

            player_data.append({
                "id": p["id"],
                "full_name": p["full_name"],
                "position": p["position"],
                "ros": ros,
                "usage": usage,
                "matchup": matchup,
                "injury": injury,
                "community": community,
                "boom": boom,
                "bust": bust,
            })

        # Calculate composite scores
        for pd in player_data:
            score, breakdown = compute_composite_score(
                pd["ros"], all_ros,
                pd["usage"], all_usage,
                pd["matchup"], all_matchup,
                pd["injury"],
                pd["community"], all_community,
            )

            # Trade value = composite score normalized to 0-100
            trade_value = score

            await db.execute("""
                UPDATE player SET composite_score = ?, trade_value = ?,
                    boom_probability = ?, bust_probability = ?
                WHERE id = ?
            """, (score, trade_value, pd["boom"], pd["bust"], pd["id"]))

        await db.commit()
        print(f"Updated composite scores for {len(player_data)} players")
    except Exception as e:
        print(f"Composite score update error: {e}")
    finally:
        await db.close()
