"""
Compact team status report, printed to the deploy logs after bootstrap.
Gives an at-a-glance view of the user's team without opening the app:
record, lineup alerts, recommended swaps, and top waiver targets.
"""
from ..database import get_db
from ..utils.constants import UNAVAILABLE_STATUSES


async def print_team_report():
    """Print the user's team status to stdout (visible in deploy logs)."""
    db = await get_db()
    try:
        league = await db.execute_fetchall(
            "SELECT name, current_week FROM league LIMIT 1"
        )
        if not league:
            print("Team report: league not synced yet")
            return
        week = league[0]["current_week"]

        team = await db.execute_fetchall("""
            SELECT id, team_name, wins, losses, ties, points_for, points_against
            FROM team WHERE is_user_team = 1 LIMIT 1
        """)
        if not team:
            print("Team report: user team not identified (use set-user-team)")
            return
        t = dict(team[0])

        print("=" * 60)
        print(f"TEAM REPORT — {t['team_name']} — Week {week}")
        print(f"Record: {t['wins']}-{t['losses']}-{t['ties']}  "
              f"PF: {t['points_for']:.1f}  PA: {t['points_against']:.1f}")
    finally:
        await db.close()

    # Lineup advice (engine opens its own connection)
    try:
        from ..engine.lineup_advisor import get_lineup_advice
        advice = await get_lineup_advice(t["id"], week)

        current = await _current_starters(t["id"])
        recommended = {s["player_name"] for s in advice["starters"]}

        alerts = []
        for p in current:
            if p["injury_status"] in UNAVAILABLE_STATUSES:
                alerts.append(f"  !! {p['full_name']} ({p['position']}, {p['slot']}) is {p['injury_status']}")
            elif p["injury_status"] in ("QUESTIONABLE", "DOUBTFUL"):
                alerts.append(f"  ?  {p['full_name']} ({p['position']}, {p['slot']}) is {p['injury_status']}")
        bench_alerts = [
            b for b in advice["bench"]
            if b.get("on_bye") or b.get("injury_status") in UNAVAILABLE_STATUSES
        ]

        print(f"Current starters not in recommended lineup: "
              f"{sorted({p['full_name'] for p in current} - recommended) or 'none'}")
        print("Lineup alerts:" if alerts else "Lineup alerts: none")
        for a in alerts:
            print(a)
        if bench_alerts:
            print("Unavailable this week (benched by advisor): "
                  + ", ".join(f"{b['player_name']} ({'bye' if b.get('on_bye') else b.get('injury_status')})"
                              for b in bench_alerts))

        print("Recommended lineup:")
        for s in advice["starters"]:
            print(f"  {s['recommended_slot']:>5}  {s['player_name']:<24} "
                  f"{s['position']:<3} {s.get('nfl_team') or '':<4} "
                  f"proj {s['projected_points']:.1f}  score {s['composite_score']:.0f}")
        for swap in advice["swap_suggestions"][:5]:
            print(f"  SWAP: {swap['reason']}")
    except Exception as e:
        print(f"Team report lineup section failed: {e}")

    # Waiver targets
    try:
        from ..engine.waiver_advisor import get_waiver_recommendations
        recs = await get_waiver_recommendations(t["id"], 5)
        print("Top waiver targets:")
        for r in recs:
            p = r["player"]
            drop = r.get("suggested_drop")
            drop_txt = f" (drop {drop['full_name']})" if drop else ""
            print(f"  {p['full_name']:<24} {p['position']:<3} {p.get('nfl_team') or '':<4} "
                  f"score {r['composite_score']:.0f}{drop_txt}")
    except Exception as e:
        print(f"Team report waiver section failed: {e}")

    print("=" * 60)


async def _current_starters(team_id: int) -> list[dict]:
    db = await get_db()
    try:
        rows = await db.execute_fetchall("""
            SELECT p.full_name, p.position, p.injury_status, re.slot
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ? AND re.slot NOT IN ('BE', 'IR')
        """, (team_id,))
        return [dict(r) for r in rows]
    finally:
        await db.close()
