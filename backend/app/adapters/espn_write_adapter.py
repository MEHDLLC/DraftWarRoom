"""
ESPN Fantasy Football WRITE adapter (unofficial).

Sends lineup transactions to the same undocumented endpoint ESPN's own web
app uses, authenticated with the stored espn_s2/SWID cookies. Everything
here is dual-gated:

- callers pass ``confirm`` to distinguish previews from real submissions
- the ESPN_WRITE_ENABLED setting must be true for anything to be sent;
  otherwise the exact payload is logged (for validation against a request
  captured in browser DevTools) and nothing leaves the box.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from ..config import get_settings
from ..utils.constants import SLOT_TO_ID

logger = logging.getLogger(__name__)

_WRITE_BASE_URL = "https://lm-api-writes.fantasy.espn.com/apis/v3/games/ffl"
_HTTP_TIMEOUT = 30.0


def compute_lineup_moves(
    roster: list[dict[str, Any]],
    recommended_slots: dict[int, str],
) -> list[dict[str, Any]]:
    """Diff the current roster against recommended slots.

    ``roster`` rows need: id (internal), espn_id, full_name, position, slot.
    ``recommended_slots`` maps internal player id -> recommended slot name;
    players absent from it are treated as bench. IR slots are never touched
    (ESPN restricts IR moves), and players without an espn_id are skipped.
    Returns a list of move dicts with from/to slot names and ids.
    """
    moves = []
    for p in roster:
        if p["slot"] == "IR" or not p.get("espn_id"):
            continue
        target = recommended_slots.get(p["id"], "BE")
        if target == p["slot"]:
            continue
        from_id = SLOT_TO_ID.get(p["slot"])
        to_id = SLOT_TO_ID.get(target)
        if from_id is None or to_id is None:
            logger.warning("Skipping move with unknown slot: %s %s->%s",
                           p["full_name"], p["slot"], target)
            continue
        moves.append({
            "player_id": p["id"],
            "espn_player_id": p["espn_id"],
            "player_name": p["full_name"],
            "position": p["position"],
            "from_slot": p["slot"],
            "to_slot": target,
            "from_slot_id": from_id,
            "to_slot_id": to_id,
        })
    # Bench moves first so slots are vacated before being filled
    moves.sort(key=lambda m: 0 if m["to_slot"] == "BE" else 1)
    return moves


def build_lineup_transaction(
    team_espn_id: int,
    week: int,
    moves: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the transaction payload ESPN's web app sends for lineup edits."""
    settings = get_settings()
    return {
        "isLeagueManager": False,
        "teamId": team_espn_id,
        "type": "ROSTER",
        "memberId": settings.espn_swid,
        "scoringPeriodId": week,
        "executionType": "EXECUTE",
        "items": [
            {
                "playerId": m["espn_player_id"],
                "type": "LINEUP",
                "fromLineupSlotId": m["from_slot_id"],
                "toLineupSlotId": m["to_slot_id"],
            }
            for m in moves
        ],
    }


async def send_transaction(payload: dict[str, Any]) -> dict[str, Any]:
    """POST a transaction to ESPN. Returns {status_code, ok, body}.

    Callers are responsible for the confirm/enabled gating; this function
    always sends.
    """
    settings = get_settings()
    url = (f"{_WRITE_BASE_URL}/seasons/{settings.nfl_season}"
           f"/segments/0/leagues/{settings.espn_league_id}/transactions/")
    cookies = {"espn_s2": settings.espn_s2, "SWID": settings.espn_swid}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Fantasy-Source": "kona",
        "X-Fantasy-Platform": "kona-PROD",
    }
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
        resp = await client.post(url, json=payload, cookies=cookies, headers=headers)
    try:
        body = resp.json()
    except Exception:
        body = resp.text[:2000]
    logger.info("ESPN write response %s: %s", resp.status_code, body)
    return {"status_code": resp.status_code, "ok": resp.is_success, "body": body}


def log_payload(payload: dict[str, Any], reason: str) -> None:
    """Print the exact payload (single write) for DevTools comparison."""
    print(f"ESPN write DRY RUN ({reason}) — payload that would be sent:\n"
          + json.dumps(payload, indent=2))
