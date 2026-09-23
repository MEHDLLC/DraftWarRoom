"""
Apply the advisor's recommended lineup to ESPN.

Shared by the /lineup/apply endpoint and the one-shot startup trigger
(APPLY_LINEUP_ON_STARTUP). All sends are gated on ESPN_WRITE_ENABLED;
without it, the exact payload is logged and nothing leaves the box.
"""
from ..config import get_settings
from ..database import get_db


async def apply_recommended_lineup(confirm: bool) -> dict:
    """Preview (confirm=False) or apply (confirm=True) the recommended lineup.

    Raises LookupError when the league or user team isn't set up.
    """
    from ..adapters.espn_write_adapter import (
        build_lineup_transaction,
        compute_lineup_moves,
        log_payload,
        send_transaction,
    )
    from ..engine.lineup_advisor import get_lineup_advice

    settings = get_settings()
    db = await get_db()
    try:
        league_rows = await db.execute_fetchall("SELECT current_week FROM league LIMIT 1")
        if not league_rows:
            raise LookupError("League not synced yet")
        week = league_rows[0]["current_week"]

        team_rows = await db.execute_fetchall(
            "SELECT id, espn_team_id FROM team WHERE is_user_team = 1 LIMIT 1"
        )
        if not team_rows:
            raise LookupError("User team not identified")
        team_id = team_rows[0]["id"]
        team_espn_id = team_rows[0]["espn_team_id"]

        roster = await db.execute_fetchall("""
            SELECT p.id, p.espn_id, p.full_name, p.position, re.slot
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ?
        """, (team_id,))
        roster = [dict(r) for r in roster]
    finally:
        await db.close()

    advice = await get_lineup_advice(team_id, week)
    recommended_slots = {s["player_id"]: s["recommended_slot"] for s in advice["starters"]}
    moves = compute_lineup_moves(roster, recommended_slots)

    public_moves = [
        {k: m[k] for k in ("player_name", "position", "from_slot", "to_slot")}
        for m in moves
    ]

    if not moves:
        return {"moves": [], "sent": False, "dry_run": False,
                "write_enabled": settings.espn_write_enabled,
                "message": "Your lineup already matches the recommendation."}

    payload = build_lineup_transaction(team_espn_id, week, moves)

    if not confirm:
        return {"moves": public_moves, "sent": False, "dry_run": True,
                "write_enabled": settings.espn_write_enabled,
                "message": f"Preview: {len(moves)} moves. Confirm to apply."}

    if not settings.espn_write_enabled:
        log_payload(payload, "ESPN_WRITE_ENABLED is off")
        return {"moves": public_moves, "sent": False, "dry_run": True,
                "write_enabled": False,
                "message": ("Dry run: writes are disabled. The exact payload was "
                            "logged to the server logs for validation. Set "
                            "ESPN_WRITE_ENABLED=true to go live.")}

    result = await send_transaction(payload)
    if result["ok"]:
        # Refresh rosters so the app reflects the new lineup
        import asyncio
        from .sync_league import sync_league_data
        asyncio.create_task(sync_league_data())
        return {"moves": public_moves, "sent": True, "dry_run": False,
                "write_enabled": True, "espn_status": result["status_code"],
                "message": f"Applied {len(moves)} moves to your ESPN lineup."}

    return {"moves": public_moves, "sent": False, "dry_run": False,
            "write_enabled": True, "espn_status": result["status_code"],
            "espn_response": result["body"],
            "message": f"ESPN rejected the transaction (HTTP {result['status_code']}). "
                       "Locked players or an invalid move are the usual causes."}
