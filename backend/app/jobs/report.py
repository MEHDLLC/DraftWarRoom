"""
Compact team status report, printed to the deploy logs after bootstrap.
Gives an at-a-glance view of the user's team without opening the app:
record, lineup alerts, recommended swaps, and top waiver targets.

The whole report is emitted as ONE print call: the log pipeline stores each
write as a single entry, so a multi-line string stays ordered and complete,
while separate prints in the same millisecond can arrive scrambled.
"""
import json

from ..database import get_db
from ..utils.constants import UNAVAILABLE_STATUSES


async def print_team_report():
    """Print the user's team status to stdout (visible in deploy logs)."""
    lines: list[str] = ["=" * 60]

    db = await get_db()
    try:
        league = await db.execute_fetchall(
            "SELECT name, current_week, roster_slots FROM league LIMIT 1"
        )
        if not league:
            print("Team report: league not synced yet")
            return
        week = league[0]["current_week"]
        slot_config = league[0]["roster_slots"]

        team = await db.execute_fetchall("""
            SELECT id, team_name, wins, losses, ties, points_for, points_against
            FROM team WHERE is_user_team = 1 LIMIT 1
        """)
        if not team:
            print("Team report: user team not identified (use set-user-team)")
            return
        t = dict(team[0])

        lines.append(f"TEAM REPORT — {t['team_name']} — Week {week}")
        lines.append(f"Record: {t['wins']}-{t['losses']}-{t['ties']}  "
                     f"PF: {t['points_for']:.1f}  PA: {t['points_against']:.1f}")

        roster = await db.execute_fetchall("""
            SELECT p.full_name, p.position, p.nfl_team, p.injury_status, re.slot
            FROM roster_entry re JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ?
        """, (t["id"],))
        roster = [dict(r) for r in roster]
        current = [p for p in roster if p["slot"] not in ("BE", "IR")]

        sched = await db.execute_fetchall(
            "SELECT nfl_team FROM nfl_team_schedule WHERE week = ?", (week,)
        )
        teams_playing = {r["nfl_team"] for r in sched}
        lines.append(f"Roster: {len(roster)} players ({len(current)} starters); "
                     f"teams playing week {week}: {len(teams_playing)}; "
                     f"slots: {slot_config}")
    finally:
        await db.close()

    # Lineup advice (engine opens its own connection)
    try:
        from ..engine.lineup_advisor import get_lineup_advice
        advice = await get_lineup_advice(t["id"], week)

        recommended = {s["player_name"] for s in advice["starters"]}
        not_recommended = sorted({p["full_name"] for p in current} - recommended)
        lines.append(f"Current starters not in recommended lineup: {not_recommended or 'none'}")

        alerts = []
        for p in current:
            if p["injury_status"] in UNAVAILABLE_STATUSES:
                alerts.append(f"  !! {p['full_name']} ({p['position']}, {p['slot']}) is {p['injury_status']}")
            elif p["injury_status"] in ("QUESTIONABLE", "DOUBTFUL"):
                alerts.append(f"  ?  {p['full_name']} ({p['position']}, {p['slot']}) is {p['injury_status']}")
            if p["nfl_team"] and teams_playing and p["nfl_team"] not in teams_playing:
                alerts.append(f"  !! {p['full_name']} ({p['position']}, {p['slot']}) is on BYE")
        lines.append("Lineup alerts:" if alerts else "Lineup alerts: none")
        lines.extend(alerts)

        bench_alerts = [
            b for b in advice["bench"]
            if b.get("on_bye") or b.get("injury_status") in UNAVAILABLE_STATUSES
        ]
        if bench_alerts:
            lines.append("Unavailable this week (benched by advisor): "
                         + ", ".join(f"{b['player_name']} ({'bye' if b.get('on_bye') else b.get('injury_status')})"
                                     for b in bench_alerts))

        lines.append(f"Recommended lineup ({len(advice['starters'])} starters):")
        for s in advice["starters"]:
            lines.append(f"  {s['recommended_slot']:>5}  {s['player_name']:<24} "
                         f"{s['position']:<3} {s.get('nfl_team') or '':<4} "
                         f"proj {s.get('projected_points') or 0:.1f}  "
                         f"score {s.get('composite_score') or 0:.0f}")
        for swap in advice["swap_suggestions"][:5]:
            lines.append(f"  SWAP: {swap['reason']}")
    except Exception as e:
        lines.append(f"Team report lineup section failed: {e!r}")

    # Waiver targets
    try:
        from ..engine.waiver_advisor import get_waiver_recommendations
        recs = await get_waiver_recommendations(t["id"], 5)
        lines.append("Top waiver targets:")
        for r in recs:
            p = r["player"]
            drop = r.get("suggested_drop")
            drop_txt = f" (drop {drop['full_name']})" if drop else ""
            lines.append(f"  {p['full_name']:<24} {p['position']:<3} {p.get('nfl_team') or '':<4} "
                         f"proj {p.get('weekly_projection') or 0:.1f}  "
                         f"score {r['composite_score']:.0f}{drop_txt}")
    except Exception as e:
        lines.append(f"Team report waiver section failed: {e!r}")

    lines.append("=" * 60)
    print("\n".join(lines))
