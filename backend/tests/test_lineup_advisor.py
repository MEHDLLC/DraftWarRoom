"""Tests for lineup advisor availability filtering and weekly projections."""
import pytest

from backend.app import database
from backend.app.database import run_migrations, get_db
from backend.app.engine.lineup_advisor import get_lineup_advice
from backend.app.utils.constants import (
    normalize_injury_status,
    normalize_nfl_team,
    normalize_position,
)


def test_normalize_nfl_team():
    assert normalize_nfl_team("LA") == "LAR"
    assert normalize_nfl_team("WAS") == "WSH"
    assert normalize_nfl_team("KC") == "KC"
    assert normalize_nfl_team(None) is None


def test_normalize_position():
    assert normalize_position("D/ST") == "DST"
    assert normalize_position("DEF") == "DST"
    assert normalize_position("RB") == "RB"


def test_normalize_injury_status():
    assert normalize_injury_status("IR") == "INJURED_RESERVE"
    assert normalize_injury_status("INJURY_RESERVE") == "INJURED_RESERVE"
    assert normalize_injury_status("Questionable") == "QUESTIONABLE"
    assert normalize_injury_status("Sus") == "SUSPENSION"
    assert normalize_injury_status(None) is None


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    return database.DB_PATH


async def _seed(week: int, players: list[dict], schedule_teams: list[str]):
    """Create a league, one team, the given players, and week schedule rows."""
    await run_migrations()
    db = await get_db()
    try:
        await db.execute("""
            INSERT INTO league (espn_id, name, season, current_week, num_teams,
                                scoring_type, roster_slots)
            VALUES (1, 'Test', 2026, ?, 10, 'PPR',
                    '{"QB": 1, "RB": 1, "FLEX": 1}')
        """, (week,))
        await db.execute("""
            INSERT INTO team (espn_team_id, league_id, team_name, is_user_team)
            VALUES (1, 1, 'My Team', 1)
        """)
        for i, p in enumerate(players, start=1):
            await db.execute("""
                INSERT INTO player (id, espn_id, full_name, position, nfl_team,
                                    composite_score, weekly_projection, injury_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (i, i, p["name"], p["position"], p["team"],
                  p["score"], p.get("weekly", 0), p.get("injury")))
            await db.execute("""
                INSERT INTO roster_entry (team_id, player_id, slot)
                VALUES (1, ?, 'BE')
            """, (i,))
        for team in schedule_teams:
            await db.execute("""
                INSERT INTO nfl_team_schedule (nfl_team, week, opponent, is_home)
                VALUES (?, ?, 'OPP', 1)
            """, (team, week))
        await db.commit()
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_out_players_never_recommended_as_starters(test_db):
    await _seed(3, [
        # Elite score but OUT — must not start
        {"name": "Star RB", "position": "RB", "team": "KC", "score": 95,
         "weekly": 20, "injury": "OUT"},
        {"name": "Backup RB", "position": "RB", "team": "SF", "score": 55, "weekly": 11},
        {"name": "QB One", "position": "QB", "team": "BUF", "score": 80, "weekly": 19},
        {"name": "Flex WR", "position": "WR", "team": "DET", "score": 60, "weekly": 12},
    ], schedule_teams=["KC", "SF", "BUF", "DET"])

    advice = await get_lineup_advice(1, 3)
    starter_names = {s["player_name"] for s in advice["starters"]}
    assert "Star RB" not in starter_names
    assert "Backup RB" in starter_names
    bench_star = next(b for b in advice["bench"] if b["player_name"] == "Star RB")
    assert "OUT" in bench_star["explanation"]
    # Swap suggestions must not propose starting the OUT player
    assert all(s["bench_player"] != "Star RB" for s in advice["swap_suggestions"])


@pytest.mark.asyncio
async def test_bye_week_players_benched(test_db):
    await _seed(5, [
        # DET has no game in week 5 -> on bye
        {"name": "Bye RB", "position": "RB", "team": "DET", "score": 90, "weekly": 0},
        {"name": "Active RB", "position": "RB", "team": "KC", "score": 50, "weekly": 10},
        {"name": "QB One", "position": "QB", "team": "BUF", "score": 70, "weekly": 18},
        {"name": "Flex WR", "position": "WR", "team": "SF", "score": 45, "weekly": 9},
    ], schedule_teams=["KC", "BUF", "SF"])

    advice = await get_lineup_advice(1, 5)
    starter_names = {s["player_name"] for s in advice["starters"]}
    assert "Bye RB" not in starter_names
    assert "Active RB" in starter_names
    bye_entry = next(b for b in advice["bench"] if b["player_name"] == "Bye RB")
    assert bye_entry["on_bye"] is True
    assert "bye" in bye_entry["explanation"].lower()


@pytest.mark.asyncio
async def test_no_schedule_data_benches_nobody(test_db):
    # Without schedule rows nobody should be treated as on bye
    await _seed(2, [
        {"name": "RB A", "position": "RB", "team": "DET", "score": 80, "weekly": 15},
        {"name": "QB A", "position": "QB", "team": "BUF", "score": 70, "weekly": 17},
    ], schedule_teams=[])

    advice = await get_lineup_advice(1, 2)
    starter_names = {s["player_name"] for s in advice["starters"]}
    assert {"RB A", "QB A"} <= starter_names
    # Weekly projection is surfaced, not the season total
    rb = next(s for s in advice["starters"] if s["player_name"] == "RB A")
    assert rb["projected_points"] == 15


@pytest.mark.asyncio
async def test_empty_slot_config_falls_back_to_default(test_db):
    """A league synced with roster_slots='{}' must not bench everyone."""
    await _seed(2, [
        {"name": "RB A", "position": "RB", "team": "DET", "score": 80, "weekly": 15},
        {"name": "QB A", "position": "QB", "team": "BUF", "score": 70, "weekly": 17},
    ], schedule_teams=[])
    db = await get_db()
    try:
        await db.execute("UPDATE league SET roster_slots = '{}'")
        await db.commit()
    finally:
        await db.close()

    advice = await get_lineup_advice(1, 2)
    starter_names = {s["player_name"] for s in advice["starters"]}
    assert {"RB A", "QB A"} <= starter_names
