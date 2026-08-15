"""
Sleeper API adapter.

Fetches trending-player and player-metadata information from the public
Sleeper API.  No authentication is required.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

SLEEPER_BASE_URL = "https://api.sleeper.app/v1"

# In-memory cache for the large ``/players/nfl`` payload.
_players_cache: dict[str, Any] | None = None
_players_cache_ts: float = 0.0
_PLAYERS_CACHE_TTL = 86_400  # 24 hours in seconds

_HTTP_TIMEOUT = 30.0  # seconds


# ---------------------------------------------------------------------------
# Trending players
# ---------------------------------------------------------------------------

def get_trending_players(
    sport: str = "nfl",
    type: str = "add",
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Return a list of trending-player dicts from Sleeper.

    Each dict contains ``player_id`` (str) and ``count`` (int).

    Parameters
    ----------
    sport:
        Sport key (default ``"nfl"``).
    type:
        Either ``"add"`` for trending adds or ``"drop"`` for trending drops.
    limit:
        Maximum number of results.
    """
    url = f"{SLEEPER_BASE_URL}/players/{sport}/trending/{type}"
    try:
        response = httpx.get(url, params={"limit": limit}, timeout=_HTTP_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return [
                {
                    "player_id": entry.get("player_id", ""),
                    "count": entry.get("count", 0),
                }
                for entry in data
            ]
        return []
    except httpx.HTTPStatusError as exc:
        logger.error("Sleeper trending players HTTP error: %s", exc.response.status_code)
        return []
    except Exception as exc:
        logger.error("Failed to fetch trending players from Sleeper: %s", exc)
        return []


# ---------------------------------------------------------------------------
# All players (cached)
# ---------------------------------------------------------------------------

def get_all_players() -> dict[str, Any]:
    """Return the full Sleeper player map (``sleeper_id`` -> player info).

    The response is large (~40 MB), so it is cached in memory for 24 hours.
    Subsequent calls within the TTL return the cached copy.
    """
    global _players_cache, _players_cache_ts  # noqa: PLW0603

    now = time.time()
    if _players_cache is not None and (now - _players_cache_ts) < _PLAYERS_CACHE_TTL:
        return _players_cache

    url = f"{SLEEPER_BASE_URL}/players/nfl"
    try:
        response = httpx.get(url, timeout=60.0)  # longer timeout for large payload
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            _players_cache = data
            _players_cache_ts = now
            logger.info("Sleeper all-players cache refreshed (%d players)", len(data))
            return data
        logger.warning("Unexpected Sleeper /players/nfl response type: %s", type(data))
        return {}
    except httpx.HTTPStatusError as exc:
        logger.error("Sleeper all-players HTTP error: %s", exc.response.status_code)
        return _players_cache if _players_cache is not None else {}
    except Exception as exc:
        logger.error("Failed to fetch all players from Sleeper: %s", exc)
        return _players_cache if _players_cache is not None else {}


# ---------------------------------------------------------------------------
# Player injuries
# ---------------------------------------------------------------------------

def get_player_injuries() -> list[dict[str, Any]]:
    """Return a list of players that currently have an injury status set.

    Each dict mirrors the Sleeper player object but is guaranteed to have a
    non-empty ``injury_status`` field.
    """
    all_players = get_all_players()
    injured: list[dict[str, Any]] = []
    try:
        for player_id, info in all_players.items():
            if not isinstance(info, dict):
                continue
            injury_status = info.get("injury_status")
            if injury_status and injury_status not in ("", None):
                injured.append({
                    "player_id": player_id,
                    "full_name": info.get("full_name", ""),
                    "first_name": info.get("first_name", ""),
                    "last_name": info.get("last_name", ""),
                    "position": info.get("position", ""),
                    "team": info.get("team", ""),
                    "injury_status": injury_status,
                    "injury_body_part": info.get("injury_body_part", ""),
                    "injury_notes": info.get("injury_notes", ""),
                    "injury_start_date": info.get("injury_start_date", ""),
                    "practice_participation": info.get("practice_participation", ""),
                })
    except Exception as exc:
        logger.error("Failed to filter injured players: %s", exc)
    return injured
