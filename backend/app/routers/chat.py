from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from ..database import get_db
from ..schemas.models import ChatRequest, ChatResponse
from ..config import get_settings

router = APIRouter()


async def _get_league_context(db) -> str:
    """Build a context string with current league state for the AI assistant."""
    parts = []

    # League info
    league_rows = await db.execute_fetchall("SELECT * FROM league LIMIT 1")
    if league_rows:
        lr = league_rows[0]
        parts.append(
            f"League: {lr['name']}, Season {lr['season']}, "
            f"Week {lr['current_week']}, {lr['num_teams']} teams, {lr['scoring_type']} scoring."
        )

    # User team
    team_rows = await db.execute_fetchall("SELECT * FROM team WHERE is_user_team = 1 LIMIT 1")
    if team_rows:
        tr = team_rows[0]
        parts.append(
            f"User's team: {tr['team_name']} ({tr['owner_name']}), "
            f"Record: {tr['wins']}-{tr['losses']}"
            + (f"-{tr['ties']}" if tr["ties"] else "")
            + f", PF: {tr['points_for']:.1f}, PA: {tr['points_against']:.1f}."
        )

        # User roster
        roster = await db.execute_fetchall(
            """
            SELECT p.full_name, p.position, p.projected_points, p.composite_score,
                   p.injury_status, re.slot
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ?
            ORDER BY CASE re.slot
                WHEN 'QB' THEN 1 WHEN 'RB' THEN 2 WHEN 'WR' THEN 3
                WHEN 'TE' THEN 4 WHEN 'FLEX' THEN 5 WHEN 'K' THEN 6
                WHEN 'DST' THEN 7 WHEN 'BE' THEN 8 WHEN 'IR' THEN 9
            END
            """,
            (tr["id"],),
        )
        if roster:
            roster_lines = []
            for r in roster:
                injury = f" [{r['injury_status']}]" if r["injury_status"] else ""
                roster_lines.append(
                    f"  {r['slot']}: {r['full_name']} ({r['position']}) "
                    f"- Proj: {r['projected_points'] or 0:.1f}{injury}"
                )
            parts.append("Current roster:\n" + "\n".join(roster_lines))

    return "\n".join(parts)


@router.post("/message")
async def send_message(request: ChatRequest):
    """Send a chat message and get a streaming response from Claude."""
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=503,
            detail="Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env",
        )

    db = await get_db()
    try:
        # Save user message
        await db.execute(
            "INSERT INTO chat_message (role, content) VALUES (?, ?)",
            ("user", request.message),
        )
        await db.commit()

        # Get recent chat history for context
        history_rows = await db.execute_fetchall(
            """
            SELECT role, content FROM chat_message
            ORDER BY created_at DESC LIMIT 20
            """
        )
        messages = [
            {"role": r["role"], "content": r["content"]}
            for r in reversed(history_rows)
        ]

        # Build league context
        league_context = await _get_league_context(db)

        system_prompt = (
            "You are DraftWarRoom, an expert fantasy football assistant. "
            "You help users manage their fantasy football team with data-driven advice. "
            "Be concise, specific, and actionable. Reference player stats and matchups "
            "when relevant. Here is the user's current league context:\n\n"
            f"{league_context}"
        )
    finally:
        await db.close()

    # Stream response from Claude
    try:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=settings.anthropic_api_key)

        async def generate():
            full_response = ""
            async with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
            ) as stream:
                async for text in stream.text_stream:
                    full_response += text
                    yield text

            # Save assistant response after streaming completes
            save_db = await get_db()
            try:
                await save_db.execute(
                    "INSERT INTO chat_message (role, content, context_summary) VALUES (?, ?, ?)",
                    ("assistant", full_response, league_context[:500]),
                )
                await save_db.commit()
            finally:
                await save_db.close()

        return StreamingResponse(generate(), media_type="text/plain")

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="anthropic package not installed. Run: pip install anthropic",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claude API error: {str(e)}")


@router.get("/history", response_model=list[ChatResponse])
async def get_chat_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Get chat message history."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """
            SELECT role, content FROM chat_message
            ORDER BY created_at ASC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return [
            ChatResponse(role=r["role"], content=r["content"])
            for r in rows
        ]
    finally:
        await db.close()
