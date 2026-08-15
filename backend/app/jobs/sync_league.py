"""
Sync league data from ESPN into local SQLite database.
"""
import json
from ..database import get_db
from ..config import get_settings
from ..utils.constants import POSITION_SLOTS


async def sync_league_data():
    """Full league sync: settings, teams, rosters, matchups, draft."""
    from ..adapters.espn_adapter import get_league, get_league_settings, get_teams, get_rosters, get_matchups, get_draft_results

    settings = get_settings()
    league = get_league()
    league_info = get_league_settings(league)
    db = await get_db()

    try:
        # Upsert league
        await db.execute("""
            INSERT INTO league (espn_id, name, season, current_week, num_teams, scoring_type,
                                playoff_start_week, roster_slots)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(espn_id) DO UPDATE SET
                name=excluded.name, current_week=excluded.current_week,
                num_teams=excluded.num_teams, scoring_type=excluded.scoring_type,
                playoff_start_week=excluded.playoff_start_week,
                roster_slots=excluded.roster_slots,
                updated_at=CURRENT_TIMESTAMP
        """, (
            settings.espn_league_id, league_info["name"], league_info["season"],
            league_info["current_week"], league_info["num_teams"],
            league_info["scoring_type"], league_info.get("playoff_start_week", 15),
            json.dumps(league_info.get("roster_slots", {})),
        ))
        await db.commit()

        # Get league DB id
        cursor = await db.execute("SELECT id FROM league WHERE espn_id = ?", (settings.espn_league_id,))
        league_row = await cursor.fetchone()
        league_id = league_row["id"]

        # Sync teams
        teams = get_teams(league)
        for team in teams:
            await db.execute("""
                INSERT INTO team (espn_team_id, league_id, owner_name, team_name, abbreviation,
                                  wins, losses, ties, points_for, points_against, streak, waiver_rank)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(espn_team_id, league_id) DO UPDATE SET
                    owner_name=excluded.owner_name, team_name=excluded.team_name,
                    wins=excluded.wins, losses=excluded.losses, ties=excluded.ties,
                    points_for=excluded.points_for, points_against=excluded.points_against,
                    streak=excluded.streak, waiver_rank=excluded.waiver_rank,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                team["espn_team_id"], league_id, team.get("owner_name"),
                team["team_name"], team.get("abbreviation"),
                team.get("wins", 0), team.get("losses", 0), team.get("ties", 0),
                team.get("points_for", 0), team.get("points_against", 0),
                team.get("streak"), team.get("waiver_rank"),
            ))
        await db.commit()

        # Sync rosters
        rosters = get_rosters(league)
        for espn_team_id, players in rosters.items():
            # Get team DB id
            cursor = await db.execute(
                "SELECT id FROM team WHERE espn_team_id = ? AND league_id = ?",
                (espn_team_id, league_id)
            )
            team_row = await cursor.fetchone()
            if not team_row:
                continue
            team_db_id = team_row["id"]

            # Clear existing roster
            await db.execute("DELETE FROM roster_entry WHERE team_id = ?", (team_db_id,))

            for player in players:
                # Upsert player
                await db.execute("""
                    INSERT INTO player (espn_id, full_name, position, nfl_team, status,
                                        injury_status, projected_points, headshot_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(espn_id) DO UPDATE SET
                        full_name=excluded.full_name, position=excluded.position,
                        nfl_team=excluded.nfl_team, status=excluded.status,
                        injury_status=excluded.injury_status,
                        projected_points=excluded.projected_points,
                        headshot_url=excluded.headshot_url,
                        updated_at=CURRENT_TIMESTAMP
                """, (
                    player["espn_id"], player["full_name"], player["position"],
                    player.get("nfl_team"), player.get("status"),
                    player.get("injury_status"), player.get("projected_points", 0),
                    player.get("headshot_url"),
                ))

                # Get player DB id
                cursor = await db.execute("SELECT id FROM player WHERE espn_id = ?", (player["espn_id"],))
                player_row = await cursor.fetchone()
                if not player_row:
                    continue

                # Add roster entry
                slot = player.get("slot", "BE")
                await db.execute("""
                    INSERT OR IGNORE INTO roster_entry (team_id, player_id, slot, acquisition_type)
                    VALUES (?, ?, ?, ?)
                """, (team_db_id, player_row["id"], slot, player.get("acquisition_type")))

        await db.commit()

        # Sync matchups for current week and past weeks
        current_week = league_info["current_week"]
        for week in range(1, current_week + 1):
            matchups = get_matchups(league, week)
            for m in matchups:
                # Get team DB ids
                home_cursor = await db.execute(
                    "SELECT id FROM team WHERE espn_team_id = ? AND league_id = ?",
                    (m["home_team_id"], league_id)
                )
                away_cursor = await db.execute(
                    "SELECT id FROM team WHERE espn_team_id = ? AND league_id = ?",
                    (m["away_team_id"], league_id)
                )
                home_row = await home_cursor.fetchone()
                away_row = await away_cursor.fetchone()
                if not home_row or not away_row:
                    continue

                home_db_id = home_row["id"]
                away_db_id = away_row["id"]

                # Determine winner
                winner_id = None
                if m.get("home_score") is not None and m.get("away_score") is not None:
                    if m["home_score"] > m["away_score"]:
                        winner_id = home_db_id
                    elif m["away_score"] > m["home_score"]:
                        winner_id = away_db_id

                await db.execute("""
                    INSERT INTO matchup (league_id, week, home_team_id, away_team_id,
                                         home_score, away_score, home_projected, away_projected,
                                         winner_team_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(league_id, week, home_team_id) DO UPDATE SET
                        home_score=excluded.home_score, away_score=excluded.away_score,
                        home_projected=excluded.home_projected, away_projected=excluded.away_projected,
                        winner_team_id=excluded.winner_team_id
                """, (
                    league_id, week, home_db_id, away_db_id,
                    m.get("home_score"), m.get("away_score"),
                    m.get("home_projected"), m.get("away_projected"),
                    winner_id,
                ))
        await db.commit()

        # Sync draft
        try:
            draft_picks = get_draft_results(league)
            for pick in draft_picks:
                espn_player_id = pick.get("espn_player_id")
                espn_team_id = pick.get("team_id")  # adapter uses "team_id" key
                if not espn_player_id or not espn_team_id:
                    continue

                # Ensure player exists
                cursor = await db.execute("SELECT id FROM player WHERE espn_id = ?", (espn_player_id,))
                p_row = await cursor.fetchone()
                if not p_row:
                    # Insert player stub from draft data
                    await db.execute("""
                        INSERT OR IGNORE INTO player (espn_id, full_name, position, nfl_team)
                        VALUES (?, ?, ?, ?)
                    """, (espn_player_id, pick.get("player_name", "Unknown"), "??", None))
                    cursor = await db.execute("SELECT id FROM player WHERE espn_id = ?", (espn_player_id,))
                    p_row = await cursor.fetchone()

                cursor = await db.execute(
                    "SELECT id FROM team WHERE espn_team_id = ? AND league_id = ?",
                    (espn_team_id, league_id)
                )
                t_row = await cursor.fetchone()

                if p_row and t_row:
                    await db.execute("""
                        INSERT OR IGNORE INTO draft_pick
                        (league_id, team_id, player_id, round, pick_number, overall_pick)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (league_id, t_row["id"], p_row["id"],
                          pick["round"], pick["pick_number"], pick["overall_pick"]))
            await db.commit()
        except Exception:
            pass  # Draft data may not be available

        print(f"League sync complete: {len(teams)} teams, {sum(len(v) for v in rosters.values())} players")

    finally:
        await db.close()
