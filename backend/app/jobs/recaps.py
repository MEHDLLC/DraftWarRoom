"""
Monday recap generation using Claude for narrative content.
"""
from ..database import get_db
from ..config import get_settings


async def generate_claude_recap():
    """Generate an AI-written weekly recap narrative."""
    from ..adapters.anthropic_adapter import chat

    db = await get_db()
    try:
        league_row = await db.execute_fetchall("SELECT current_week FROM league LIMIT 1")
        if not league_row:
            return None
        last_week = league_row[0]["current_week"] - 1
        if last_week < 1:
            return None

        # Get all matchup results
        matchups = await db.execute_fetchall("""
            SELECT m.week, m.home_score, m.away_score,
                   t1.team_name as home_name, t2.team_name as away_name,
                   t1.is_user_team as home_is_user, t2.is_user_team as away_is_user
            FROM matchup m
            JOIN team t1 ON t1.id = m.home_team_id
            JOIN team t2 ON t2.id = m.away_team_id
            WHERE m.week = ?
        """, (last_week,))

        if not matchups:
            return None

        # Build context for Claude
        results = []
        user_result = None
        for m in matchups:
            m = dict(m)
            winner = m["home_name"] if (m["home_score"] or 0) > (m["away_score"] or 0) else m["away_name"]
            results.append(f"{m['home_name']} {m['home_score']:.1f} vs {m['away_name']} {m['away_score']:.1f} (Winner: {winner})")
            if m["home_is_user"] or m["away_is_user"]:
                user_result = m

        context = f"Week {last_week} results:\n" + "\n".join(results)

        system_prompt = """You are a fun, witty fantasy football analyst writing a weekly recap for a casual league.
Keep it short (3-4 sentences max). Include:
1. The user's result (celebrate wins, sympathize with losses)
2. One standout performance from around the league
3. A lighthearted trash-talk line about the next opponent or the league in general.
Be fun and engaging. Use fantasy football lingo naturally."""

        messages = [{"role": "user", "content": f"Write a Week {last_week} recap.\n\n{context}"}]

        recap_text = await chat(messages, system_prompt)
        return recap_text

    except Exception as e:
        print(f"Claude recap error: {e}")
        return None
    finally:
        await db.close()
