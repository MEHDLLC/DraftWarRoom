"""
Notification creation service and pre-kickoff lineup guardrails.
"""
import json
from ..database import get_db


async def create_notification(
    title: str,
    body: str,
    type: str,
    priority: str = "normal",
    data: dict | None = None,
):
    """Create a new in-app notification."""
    db = await get_db()
    try:
        await db.execute("""
            INSERT INTO notification (title, body, type, priority, data)
            VALUES (?, ?, ?, ?, ?)
        """, (title, body, type, priority, json.dumps(data) if data else None))
        await db.commit()
    finally:
        await db.close()


async def check_lineup_guardrails():
    """
    Pre-kickoff check: flag injured/bye players in starting lineup.
    Creates urgent notifications for any issues found.
    """
    db = await get_db()
    try:
        # Get user team
        team_row = await db.execute_fetchall(
            "SELECT id, team_name FROM team WHERE is_user_team = 1 LIMIT 1"
        )
        if not team_row:
            return

        team_id = team_row[0]["id"]

        # Check for injured starters
        injured_starters = await db.execute_fetchall("""
            SELECT p.full_name, p.position, p.injury_status, re.slot
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ? AND re.slot NOT IN ('BE', 'IR')
            AND p.injury_status IN ('OUT', 'DOUBTFUL', 'INJURED_RESERVE')
        """, (team_id,))

        for player in injured_starters:
            await create_notification(
                title=f"Lineup Alert: {player['full_name']}",
                body=f"{player['full_name']} ({player['position']}) is {player['injury_status']} but still in your starting lineup at {player['slot']}. Move to bench and find a replacement!",
                type="LINEUP_ALERT",
                priority="urgent",
                data={"player_name": player["full_name"], "position": player["position"]},
            )

        # Check for questionable starters (lower priority)
        questionable_starters = await db.execute_fetchall("""
            SELECT p.full_name, p.position, p.injury_status, re.slot
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ? AND re.slot NOT IN ('BE', 'IR')
            AND p.injury_status = 'QUESTIONABLE'
        """, (team_id,))

        for player in questionable_starters:
            await create_notification(
                title=f"Monitor: {player['full_name']} is Questionable",
                body=f"{player['full_name']} ({player['position']}) is Questionable for this week. Check for updates before kickoff and have a backup ready.",
                type="LINEUP_ALERT",
                priority="high",
                data={"player_name": player["full_name"], "position": player["position"]},
            )

        if injured_starters:
            print(f"Lineup guardrails: {len(injured_starters)} injured starters flagged")

    except Exception as e:
        print(f"Lineup guardrails error: {e}")
    finally:
        await db.close()


async def generate_weekly_recap():
    """Generate a Monday morning recap notification."""
    db = await get_db()
    try:
        league_row = await db.execute_fetchall("SELECT current_week FROM league LIMIT 1")
        if not league_row:
            return
        last_week = league_row[0]["current_week"] - 1
        if last_week < 1:
            return

        team_row = await db.execute_fetchall(
            "SELECT id, team_name FROM team WHERE is_user_team = 1 LIMIT 1"
        )
        if not team_row:
            return
        team_id = team_row[0]["id"]
        team_name = team_row[0]["team_name"]

        # Get last week's matchup result
        matchup = await db.execute_fetchall("""
            SELECT m.*, t1.team_name as home_name, t2.team_name as away_name
            FROM matchup m
            JOIN team t1 ON t1.id = m.home_team_id
            JOIN team t2 ON t2.id = m.away_team_id
            WHERE (m.home_team_id = ? OR m.away_team_id = ?) AND m.week = ?
        """, (team_id, team_id, last_week))

        if not matchup:
            return

        m = dict(matchup[0])
        is_home = m["home_team_id"] == team_id
        your_score = m["home_score"] if is_home else m["away_score"]
        opp_score = m["away_score"] if is_home else m["home_score"]
        opp_name = m["away_name"] if is_home else m["home_name"]
        won = your_score > opp_score if your_score and opp_score else None

        if won is None:
            return

        if won:
            title = f"Week {last_week} Win! {your_score:.1f} - {opp_score:.1f}"
            body = f"Great week! You beat {opp_name} by {your_score - opp_score:.1f} points."
        else:
            title = f"Week {last_week} Loss: {your_score:.1f} - {opp_score:.1f}"
            body = f"Tough loss to {opp_name} by {opp_score - your_score:.1f} points. Time to bounce back!"

        await create_notification(
            title=title,
            body=body,
            type="RECAP",
            priority="normal",
            data={"week": last_week, "won": won, "score": your_score, "opp_score": opp_score},
        )

    except Exception as e:
        print(f"Weekly recap error: {e}")
    finally:
        await db.close()


async def check_waiver_opportunities():
    """Tuesday notification about top waiver wire targets."""
    db = await get_db()
    try:
        # Get top trending free agents
        top_fa = await db.execute_fetchall("""
            SELECT full_name, position, composite_score, sleeper_trending_add
            FROM player
            WHERE id NOT IN (SELECT player_id FROM roster_entry)
            AND composite_score > 40
            ORDER BY composite_score DESC
            LIMIT 3
        """)

        if top_fa:
            names = [f"{p['full_name']} ({p['position']})" for p in top_fa]
            await create_notification(
                title="Waiver Wire Targets",
                body=f"Top available pickups: {', '.join(names)}. Check the Waivers tab for full analysis!",
                type="WAIVER_TIP",
                priority="normal",
            )
    except Exception as e:
        print(f"Waiver check error: {e}")
    finally:
        await db.close()
