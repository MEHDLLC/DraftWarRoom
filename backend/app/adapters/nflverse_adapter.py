"""
nflverse data adapter.

Downloads CSV data published by the nflverse project on GitHub and returns
it as pandas DataFrames.  Results are cached in memory so that repeated
calls within the same process do not re-download the files.
"""

from __future__ import annotations

import io
import logging
from typing import Any

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

_WEEKLY_STATS_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/"
    "player_stats/player_stats_{season}.csv"
)
_SNAP_COUNTS_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/"
    "snap_counts/snap_counts_{season}.csv"
)

_HTTP_TIMEOUT = 60.0  # generous timeout for large CSV downloads

# In-memory caches keyed by season.
_weekly_stats_cache: dict[int, pd.DataFrame] = {}
_snap_counts_cache: dict[int, pd.DataFrame] = {}


# ---------------------------------------------------------------------------
# Weekly player stats
# ---------------------------------------------------------------------------

def get_weekly_stats(season: int) -> pd.DataFrame:
    """Download and parse weekly player stats for *season*.

    Returns a :class:`pandas.DataFrame` with one row per player-week.
    The result is cached in memory so subsequent calls are instant.
    Returns an empty ``DataFrame`` on failure.
    """
    if season in _weekly_stats_cache:
        return _weekly_stats_cache[season]

    url = _WEEKLY_STATS_URL.format(season=season)
    df = _download_csv(url, label=f"weekly_stats_{season}")
    if df is not None:
        _weekly_stats_cache[season] = df
        return df
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# Snap counts
# ---------------------------------------------------------------------------

def get_snap_counts(season: int) -> pd.DataFrame:
    """Download and parse snap-count data for *season*.

    Returns a :class:`pandas.DataFrame` with one row per player-week.
    The result is cached in memory so subsequent calls are instant.
    Returns an empty ``DataFrame`` on failure.
    """
    if season in _snap_counts_cache:
        return _snap_counts_cache[season]

    url = _SNAP_COUNTS_URL.format(season=season)
    df = _download_csv(url, label=f"snap_counts_{season}")
    if df is not None:
        _snap_counts_cache[season] = df
        return df
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _download_csv(url: str, label: str = "") -> pd.DataFrame | None:
    """Download a CSV from *url* and return it as a DataFrame.

    Returns ``None`` on any failure so callers can fall back to an empty
    DataFrame.
    """
    try:
        logger.info("Downloading nflverse data: %s", label or url)
        response = httpx.get(url, timeout=_HTTP_TIMEOUT, follow_redirects=True)
        response.raise_for_status()

        df = pd.read_csv(io.StringIO(response.text))
        logger.info(
            "nflverse %s loaded: %d rows x %d columns",
            label,
            len(df),
            len(df.columns),
        )
        return df
    except httpx.HTTPStatusError as exc:
        logger.error(
            "nflverse HTTP error for %s: %s %s",
            label,
            exc.response.status_code,
            exc.response.reason_phrase,
        )
    except pd.errors.ParserError as exc:
        logger.error("nflverse CSV parse error for %s: %s", label, exc)
    except Exception as exc:
        logger.error("Failed to download nflverse data (%s): %s", label, exc)
    return None
