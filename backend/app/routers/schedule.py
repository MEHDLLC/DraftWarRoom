from fastapi import APIRouter, HTTPException
from ..database import get_db
from ..schemas.models import ScheduleEntry

router = APIRouter()


def _matchup_grade(rank: int | None) -> str:
    """Convert a points-allowed rank (1=worst defense) to a letter grade."""
    if rank is None:
        return "C"
    if rank <= 4:
        return "A+"
    if rank <= 8:
        return "A"
    if rank <= 12:
        return "B+"
    if rank <= 16:
        return "B"
    if rank <= 20:
        return "C+"
    if rank <= 24:
        return "C"
    if rank <= 28:
        return "D"
    return "F"


def _get_pa_columns(position: str) -> tuple[str, str]:
    """Return the (rank_column, ppg_column) for a given position."""
    pos_map = {
        "QB": ("pa_qb_rank", "pa_qb_ppg"),
        "RB": ("pa_rb_rank", "pa_rb_ppg"),
        "WR": ("pa_wr_rank", "pa_wr_ppg"),
        "TE": ("pa_te_rank", "pa_te_ppg"),
        "K": ("pa_k_rank", "pa_k_ppg"),
        "DST": ("pa_dst_rank", "pa_dst_ppg"),
    }
    return pos_map.get(position.upper(), ("pa_qb_rank", "pa_qb_ppg"))


@router.get("/sos/{player_id}", response_model=list[ScheduleEntry])
async def get_strength_of_schedule(player_id: int):
    """Get remaining strength of schedule for a player based on position matchups."""
    db = await get_db()
    try:
        # Get player info
        player_rows = await db.execute_fetchall(
            "SELECT position, nfl_team FROM player WHERE id = ?",
            (player_id,),
        )
        if not player_rows:
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")

        position = player_rows[0]["position"]
        nfl_team = player_rows[0]["nfl_team"]

        if not nfl_team:
            raise HTTPException(
                status_code=400,
                detail=f"Player {player_id} has no NFL team assigned",
            )

        # Get current week
        league_rows = await db.execute_fetchall("SELECT current_week FROM league LIMIT 1")
        current_week = league_rows[0]["current_week"] if league_rows else 1

        rank_col, ppg_col = _get_pa_columns(position)

        # Get remaining schedule
        rows = await db.execute_fetchall(
            f"""
            SELECT week, opponent, is_home, {rank_col} as pa_rank, {ppg_col} as pa_ppg
            FROM nfl_team_schedule
            WHERE nfl_team = ? AND week >= ?
            ORDER BY week ASC
            """,
            (nfl_team, current_week),
        )

        return [
            ScheduleEntry(
                week=r["week"],
                opponent=r["opponent"],
                is_home=bool(r["is_home"]),
                matchup_grade=_matchup_grade(r["pa_rank"]),
                pa_rank=r["pa_rank"],
                pa_ppg=r["pa_ppg"],
            )
            for r in rows
        ]
    finally:
        await db.close()


@router.get("/playoffs")
async def get_playoff_schedule():
    """Get playoff schedule analysis showing matchup difficulty during playoff weeks."""
    db = await get_db()
    try:
        league_rows = await db.execute_fetchall(
            "SELECT playoff_start_week FROM league LIMIT 1"
        )
        if not league_rows:
            raise HTTPException(status_code=404, detail="League not synced yet")

        playoff_start = league_rows[0]["playoff_start_week"] or 15
        playoff_weeks = [playoff_start, playoff_start + 1, playoff_start + 2]

        # Get user team roster
        team_rows = await db.execute_fetchall("SELECT id FROM team WHERE is_user_team = 1 LIMIT 1")
        if not team_rows:
            raise HTTPException(status_code=404, detail="User team not identified")
        team_id = team_rows[0]["id"]

        roster = await db.execute_fetchall(
            """
            SELECT p.id, p.full_name, p.position, p.nfl_team, re.slot
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ? AND re.slot NOT IN ('BE', 'IR')
            """,
            (team_id,),
        )

        # For each starter, get their playoff matchup grades
        player_schedules = []
        for player in roster:
            if not player["nfl_team"]:
                continue

            rank_col, ppg_col = _get_pa_columns(player["position"])
            placeholders = ",".join("?" for _ in playoff_weeks)
            sched_rows = await db.execute_fetchall(
                f"""
                SELECT week, opponent, is_home, {rank_col} as pa_rank, {ppg_col} as pa_ppg
                FROM nfl_team_schedule
                WHERE nfl_team = ? AND week IN ({placeholders})
                ORDER BY week ASC
                """,
                (player["nfl_team"], *playoff_weeks),
            )

            weeks_data = []
            for sr in sched_rows:
                weeks_data.append({
                    "week": sr["week"],
                    "opponent": sr["opponent"],
                    "is_home": bool(sr["is_home"]),
                    "matchup_grade": _matchup_grade(sr["pa_rank"]),
                    "pa_rank": sr["pa_rank"],
                    "pa_ppg": sr["pa_ppg"],
                })

            player_schedules.append({
                "player_id": player["id"],
                "player_name": player["full_name"],
                "position": player["position"],
                "nfl_team": player["nfl_team"],
                "slot": player["slot"],
                "playoff_weeks": weeks_data,
            })

        return {
            "playoff_start_week": playoff_start,
            "playoff_weeks": playoff_weeks,
            "starters": player_schedules,
        }
    finally:
        await db.close()


@router.get("/byes")
async def get_bye_weeks():
    """Get bye week overview for all rostered players on user's team."""
    db = await get_db()
    try:
        # Get user team
        team_rows = await db.execute_fetchall("SELECT id FROM team WHERE is_user_team = 1 LIMIT 1")
        if not team_rows:
            raise HTTPException(status_code=404, detail="User team not identified")
        team_id = team_rows[0]["id"]

        league_rows = await db.execute_fetchall("SELECT current_week FROM league LIMIT 1")
        current_week = league_rows[0]["current_week"] if league_rows else 1

        # Get roster with NFL teams
        roster = await db.execute_fetchall(
            """
            SELECT p.id, p.full_name, p.position, p.nfl_team, re.slot
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ?
            ORDER BY CASE re.slot
                WHEN 'QB' THEN 1 WHEN 'RB' THEN 2 WHEN 'WR' THEN 3
                WHEN 'TE' THEN 4 WHEN 'FLEX' THEN 5 WHEN 'K' THEN 6
                WHEN 'DST' THEN 7 WHEN 'BE' THEN 8 WHEN 'IR' THEN 9
            END
            """,
            (team_id,),
        )

        # Find bye weeks by looking for gaps in the schedule
        bye_data = []
        bye_week_counts: dict[int, int] = {}

        for player in roster:
            if not player["nfl_team"]:
                bye_data.append({
                    "player_id": player["id"],
                    "player_name": player["full_name"],
                    "position": player["position"],
                    "nfl_team": player["nfl_team"],
                    "slot": player["slot"],
                    "bye_week": None,
                })
                continue

            # Check all 18 weeks, find the missing one (bye week)
            sched = await db.execute_fetchall(
                "SELECT week FROM nfl_team_schedule WHERE nfl_team = ? ORDER BY week",
                (player["nfl_team"],),
            )
            scheduled_weeks = {r["week"] for r in sched}
            all_weeks = set(range(1, 19))
            bye_weeks = all_weeks - scheduled_weeks

            bye_week = min(bye_weeks) if bye_weeks else None

            if bye_week:
                bye_week_counts[bye_week] = bye_week_counts.get(bye_week, 0) + 1

            bye_data.append({
                "player_id": player["id"],
                "player_name": player["full_name"],
                "position": player["position"],
                "nfl_team": player["nfl_team"],
                "slot": player["slot"],
                "bye_week": bye_week,
                "bye_passed": bye_week is not None and bye_week < current_week,
            })

        # Flag weeks with heavy byes
        trouble_weeks = [
            {"week": w, "players_on_bye": count}
            for w, count in sorted(bye_week_counts.items())
            if count >= 2 and w >= current_week
        ]

        return {
            "current_week": current_week,
            "players": bye_data,
            "trouble_weeks": trouble_weeks,
        }
    finally:
        await db.close()
