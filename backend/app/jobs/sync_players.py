"""
Sync player data from Sleeper and nflverse to enrich local database.
"""
from ..database import get_db
from ..config import get_settings
from ..engine.scorer import compute_composite_score, injury_to_score, usage_trend_score, generate_explanation
from ..engine.boom_bust import calculate_boom_bust


async def sync_sleeper_data():
    """Sync trending data and injuries from Sleeper."""
    from ..adapters.sleeper_adapter import get_trending_players, get_all_players

    db = await get_db()
    try:
        # Get trending adds and drops
        trending_adds = await get_trending_players("nfl", "add", 50)
        trending_drops = await get_trending_players("nfl", "drop", 50)

        # Get full Sleeper player database for cross-referencing
        all_sleeper = await get_all_players()

        # Map Sleeper IDs to our players by name+team
        for trend in trending_adds:
            sleeper_id = trend["player_id"]
            if sleeper_id in all_sleeper:
                sp = all_sleeper[sleeper_id]
                name = f"{sp.get('first_name', '')} {sp.get('last_name', '')}".strip()
                team = sp.get("team")
                if name and team:
                    await db.execute("""
                        UPDATE player SET sleeper_id = ?, sleeper_trending_add = ?,
                                          injury_status = COALESCE(?, injury_status)
                        WHERE full_name = ? AND nfl_team = ?
                    """, (sleeper_id, trend["count"], sp.get("injury_status"), name, team))

        for trend in trending_drops:
            sleeper_id = trend["player_id"]
            if sleeper_id in all_sleeper:
                sp = all_sleeper[sleeper_id]
                name = f"{sp.get('first_name', '')} {sp.get('last_name', '')}".strip()
                team = sp.get("team")
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
        # Weekly stats
        stats_df = await get_weekly_stats(season)
        if stats_df is not None and not stats_df.empty:
            for _, row in stats_df.iterrows():
                # Find player by name and team
                name = row.get("player_display_name") or row.get("player_name", "")
                team = row.get("recent_team", "")
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
                    player_row["id"], season, week,
                    row.get("fantasy_points_ppr", 0),
                    row.get("passing_yards", 0), row.get("passing_tds", 0),
                    row.get("interceptions", 0),
                    row.get("rushing_yards", 0), row.get("rushing_tds", 0),
                    row.get("carries", 0), row.get("receptions", 0),
                    row.get("receiving_yards", 0), row.get("receiving_tds", 0),
                    row.get("targets", 0),
                ))
            await db.commit()

        # Snap counts
        snaps_df = await get_snap_counts(season)
        if snaps_df is not None and not snaps_df.empty:
            for _, row in snaps_df.iterrows():
                name = row.get("player", "")
                team = row.get("team", "")
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
                    player_row["id"], season, week,
                ))
            await db.commit()

        print("nflverse stats sync complete")
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

        # Get all players with roster entries
        players = await db.execute_fetchall("""
            SELECT p.* FROM player p
            WHERE p.position IN ('QB', 'RB', 'WR', 'TE', 'K', 'DST')
        """)

        if not players:
            return

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
            """, (p["id"], season))

            weekly_points = [s["fantasy_points"] for s in stats if s["fantasy_points"]]
            weekly_snaps = [s["snap_pct"] for s in stats if s["snap_pct"]]

            ros = p.get("ros_projection") or p.get("projected_points") or 0
            usage = usage_trend_score(weekly_snaps)
            matchup = 50.0  # Default - would be enhanced with schedule data
            injury = injury_to_score(p.get("injury_status"))
            community = (p.get("sleeper_trending_add") or 0)

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
