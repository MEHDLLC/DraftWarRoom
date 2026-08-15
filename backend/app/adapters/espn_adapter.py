"""
ESPN Fantasy Football adapter.

Wraps the espn_api Python package to fetch league, team, roster, matchup,
draft, and free-agent data from ESPN Fantasy Football.
"""

from __future__ import annotations

import logging
from typing import Any

from espn_api.football import League

from ..config import get_settings
from ..utils.constants import POSITION_SLOTS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# League object
# ---------------------------------------------------------------------------

def get_league() -> League:
    """Return an espn_api League object for the configured league.

    Raises ``RuntimeError`` if the league cannot be fetched (bad credentials,
    network error, etc.).
    """
    settings = get_settings()
    try:
        league = League(
            league_id=settings.espn_league_id,
            year=settings.nfl_season,
            espn_s2=settings.espn_s2,
            swid=settings.espn_swid,
        )
        return league
    except Exception as exc:
        logger.error("Failed to connect to ESPN league %s: %s", settings.espn_league_id, exc)
        raise RuntimeError(f"Could not fetch ESPN league: {exc}") from exc


# ---------------------------------------------------------------------------
# League settings
# ---------------------------------------------------------------------------

def get_league_settings(league: League) -> dict[str, Any]:
    """Extract high-level league settings into a plain dict."""
    try:
        settings_obj = league.settings
        return {
            "name": getattr(settings_obj, "name", league.settings.name if hasattr(league.settings, "name") else ""),
            "season": league.year,
            "current_week": league.current_week,
            "num_teams": getattr(settings_obj, "team_count", len(league.teams)),
            "scoring_type": _resolve_scoring_type(settings_obj),
            "playoff_start_week": getattr(settings_obj, "playoff_team_count", None)
                                  or getattr(settings_obj, "reg_season_count", None),
            "roster_slots": _extract_roster_slots(settings_obj),
        }
    except Exception as exc:
        logger.error("Failed to read league settings: %s", exc)
        return {
            "name": "",
            "season": league.year,
            "current_week": getattr(league, "current_week", 1),
            "num_teams": len(league.teams) if hasattr(league, "teams") else 0,
            "scoring_type": "UNKNOWN",
            "playoff_start_week": None,
            "roster_slots": {},
        }


def _resolve_scoring_type(settings_obj: Any) -> str:
    """Best-effort extraction of the scoring format string."""
    scoring = getattr(settings_obj, "scoring_type", None)
    if scoring:
        return str(scoring)
    # Some espn_api versions expose scoring_items instead
    return "UNKNOWN"


def _extract_roster_slots(settings_obj: Any) -> dict[str, int]:
    """Return a mapping of slot name -> count from the league settings."""
    try:
        slot_counts: dict[str, int] = {}
        roster_slots = getattr(settings_obj, "roster_slots", None) or {}
        if isinstance(roster_slots, dict):
            for slot_id, count in roster_slots.items():
                name = POSITION_SLOTS.get(int(slot_id), f"SLOT_{slot_id}")
                slot_counts[name] = count
        return slot_counts
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------

def get_teams(league: League) -> list[dict[str, Any]]:
    """Return a list of team dicts from the league."""
    teams: list[dict[str, Any]] = []
    try:
        for team in league.teams:
            teams.append({
                "espn_team_id": team.team_id,
                "owner_name": getattr(team, "owner", None) or getattr(team, "owners", [""])[0] if getattr(team, "owners", None) else "",
                "team_name": team.team_name,
                "abbreviation": getattr(team, "team_abbrev", ""),
                "wins": getattr(team, "wins", 0),
                "losses": getattr(team, "losses", 0),
                "ties": getattr(team, "ties", 0),
                "points_for": round(getattr(team, "points_for", 0.0), 2),
                "points_against": round(getattr(team, "points_against", 0.0), 2),
                "streak": _team_streak(team),
            })
    except Exception as exc:
        logger.error("Failed to fetch teams: %s", exc)
    return teams


def _team_streak(team: Any) -> str:
    """Return the human-readable streak string for a team."""
    streak_type = getattr(team, "streak_type", None)
    streak_len = getattr(team, "streak_length", 0)
    if streak_type and streak_len:
        return f"{streak_type[0].upper()}{streak_len}"
    return ""


# ---------------------------------------------------------------------------
# Rosters
# ---------------------------------------------------------------------------

def get_rosters(league: League) -> dict[int, list[dict[str, Any]]]:
    """Return a dict mapping ``espn_team_id`` to a list of player dicts."""
    rosters: dict[int, list[dict[str, Any]]] = {}
    try:
        for team in league.teams:
            players: list[dict[str, Any]] = []
            for player in team.roster:
                players.append(_player_to_dict(player))
            rosters[team.team_id] = players
    except Exception as exc:
        logger.error("Failed to fetch rosters: %s", exc)
    return rosters


def _player_to_dict(player: Any) -> dict[str, Any]:
    """Convert an espn_api Player object to a flat dict."""
    # Projected points for the current scoring period
    projected = 0.0
    try:
        stats = getattr(player, "stats", {}) or {}
        for period_stats in stats.values():
            if isinstance(period_stats, dict) and "projected_points" in period_stats:
                projected = period_stats["projected_points"]
                break
        # Fallback to the top-level attribute
        if projected == 0.0:
            projected = getattr(player, "projected_points", 0.0) or 0.0
    except Exception:
        projected = getattr(player, "projected_points", 0.0) or 0.0

    return {
        "espn_id": player.playerId,
        "full_name": player.name,
        "position": player.position,
        "nfl_team": getattr(player, "proTeam", ""),
        "slot": _resolve_slot(player),
        "projected_points": round(projected, 2),
        "injury_status": getattr(player, "injuryStatus", "ACTIVE"),
        "injury_note": getattr(player, "injuryComment", None),
        "eligible_slots": [
            POSITION_SLOTS.get(s, str(s))
            for s in (getattr(player, "eligibleSlots", []) or [])
        ],
        "acquisition_type": getattr(player, "acquisitionType", None),
        "percent_owned": getattr(player, "percent_owned", None),
        "percent_started": getattr(player, "percent_started", None),
    }


def _resolve_slot(player: Any) -> str:
    """Determine the current roster slot name for a player."""
    slot_id = getattr(player, "lineupSlot", None)
    if slot_id is not None:
        return POSITION_SLOTS.get(slot_id, str(slot_id))
    return "BE"


# ---------------------------------------------------------------------------
# Player info (by ID list)
# ---------------------------------------------------------------------------

def get_player_info(league: League, player_ids: list[int]) -> list[dict[str, Any]]:
    """Fetch detailed info for a list of player IDs.

    Uses ``league.player_info()`` when available; falls back to scanning
    team rosters.
    """
    results: list[dict[str, Any]] = []
    try:
        for pid in player_ids:
            try:
                player = league.player_info(playerId=pid)
                if player:
                    info = _player_to_dict(player)
                    # Attach full stats blob when available
                    info["stats"] = _extract_stats(player)
                    results.append(info)
            except Exception as inner_exc:
                logger.warning("Could not fetch player %s: %s", pid, inner_exc)
    except Exception as exc:
        logger.error("get_player_info failed: %s", exc)
    return results


def _extract_stats(player: Any) -> dict[str, Any]:
    """Pull the raw stats dict from a Player object, if present."""
    try:
        raw = getattr(player, "stats", None)
        if raw and isinstance(raw, dict):
            return raw
    except Exception:
        pass
    return {}


# ---------------------------------------------------------------------------
# Matchups
# ---------------------------------------------------------------------------

def get_matchups(league: League, week: int) -> list[dict[str, Any]]:
    """Return matchup dicts for a given NFL week."""
    matchups: list[dict[str, Any]] = []
    try:
        box_scores = league.box_scores(week)
        for box in box_scores:
            home_team = getattr(box, "home_team", None)
            away_team = getattr(box, "away_team", None)
            matchup: dict[str, Any] = {
                "week": week,
                "home_team_id": home_team.team_id if home_team else None,
                "home_team_name": home_team.team_name if home_team else None,
                "home_score": getattr(box, "home_score", 0.0),
                "home_projected": _sum_projected(getattr(box, "home_lineup", [])),
                "away_team_id": away_team.team_id if away_team else None,
                "away_team_name": away_team.team_name if away_team else None,
                "away_score": getattr(box, "away_score", 0.0),
                "away_projected": _sum_projected(getattr(box, "away_lineup", [])),
                "home_lineup": [_boxscore_player(p) for p in getattr(box, "home_lineup", [])],
                "away_lineup": [_boxscore_player(p) for p in getattr(box, "away_lineup", [])],
            }
            matchups.append(matchup)
    except Exception as exc:
        logger.error("Failed to fetch matchups for week %s: %s", week, exc)
    return matchups


def _sum_projected(lineup: list[Any]) -> float:
    """Sum projected points for a lineup, excluding bench."""
    total = 0.0
    for p in lineup:
        slot_id = getattr(p, "slot_position", None) or getattr(p, "lineupSlot", None)
        # Bench = 20, IR = 21 in ESPN slot IDs
        if slot_id in (20, 21, "BE", "IR"):
            continue
        try:
            proj = getattr(p, "projected_points", 0.0) or 0.0
            total += proj
        except Exception:
            pass
    return round(total, 2)


def _boxscore_player(player: Any) -> dict[str, Any]:
    """Convert a box-score player entry into a dict."""
    return {
        "espn_id": getattr(player, "playerId", None),
        "name": getattr(player, "name", ""),
        "position": getattr(player, "position", ""),
        "slot": _resolve_slot(player),
        "points": getattr(player, "points", 0.0),
        "projected_points": getattr(player, "projected_points", 0.0),
    }


# ---------------------------------------------------------------------------
# Draft results
# ---------------------------------------------------------------------------

def get_draft_results(league: League) -> list[dict[str, Any]]:
    """Return a list of draft-pick dicts."""
    picks: list[dict[str, Any]] = []
    try:
        for i, pick in enumerate(league.draft):
            team = getattr(pick, "team", None)
            player_name = getattr(pick, "playerName", None)
            if player_name is None:
                player_name = getattr(pick, "player_name", "Unknown")
            picks.append({
                "round": getattr(pick, "round_num", (i // len(league.teams)) + 1),
                "pick_number": getattr(pick, "round_pick", (i % len(league.teams)) + 1),
                "overall_pick": i + 1,
                "espn_player_id": getattr(pick, "playerId", None),
                "player_name": player_name,
                "team_id": team.team_id if team else None,
                "team_name": team.team_name if team else None,
                "bid_amount": getattr(pick, "bid_amount", 0),
                "keeper": getattr(pick, "keeper_status", False),
            })
    except Exception as exc:
        logger.error("Failed to fetch draft results: %s", exc)
    return picks


# ---------------------------------------------------------------------------
# Free agents
# ---------------------------------------------------------------------------

def get_free_agents(
    league: League,
    position: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return available free agents, optionally filtered by position."""
    agents: list[dict[str, Any]] = []
    try:
        kwargs: dict[str, Any] = {"size": limit}
        if position:
            kwargs["position"] = position
        fa_list = league.free_agents(**kwargs)
        for player in fa_list:
            agents.append(_player_to_dict(player))
    except Exception as exc:
        logger.error("Failed to fetch free agents: %s", exc)
    return agents


# ---------------------------------------------------------------------------
# Points allowed by position
# ---------------------------------------------------------------------------

def get_points_allowed_by_position(league: League) -> dict[str, dict[str, Any]]:
    """Return a mapping of NFL team -> position -> points-allowed ranking.

    Attempts to use ``league.power_rankings()`` or internal ESPN
    ``settings.position_scoring`` data.  Returns an empty dict if the
    data is unavailable in the current espn_api version.
    """
    result: dict[str, dict[str, Any]] = {}
    try:
        # Some espn_api versions expose this directly
        pa_data = getattr(league, "nfl_team_pa", None)
        if pa_data and isinstance(pa_data, dict):
            return pa_data

        # Attempt box-score aggregation as a fallback
        # This is a simplified heuristic: sum points scored by position
        # against each NFL defense over recent weeks.
        current_week = getattr(league, "current_week", 1)
        weeks_to_check = range(max(1, current_week - 4), current_week)
        for week in weeks_to_check:
            try:
                boxes = league.box_scores(week)
                for box in boxes:
                    for lineup in (
                        getattr(box, "home_lineup", []),
                        getattr(box, "away_lineup", []),
                    ):
                        for player in lineup:
                            nfl_team = getattr(player, "proTeam", None)
                            pos = getattr(player, "position", None)
                            pts = getattr(player, "points", 0.0)
                            if nfl_team and pos and pts:
                                result.setdefault(nfl_team, {})
                                result[nfl_team].setdefault(pos, {"total": 0.0, "games": 0})
                                result[nfl_team][pos]["total"] += pts
                                result[nfl_team][pos]["games"] += 1
            except Exception:
                continue

        # Convert totals to per-game averages
        for team_data in result.values():
            for pos_data in team_data.values():
                if isinstance(pos_data, dict) and pos_data.get("games", 0) > 0:
                    pos_data["ppg"] = round(pos_data["total"] / pos_data["games"], 2)
    except Exception as exc:
        logger.error("Failed to compute points allowed by position: %s", exc)
    return result
