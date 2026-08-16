from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..database import get_db
from ..schemas.models import DraftPickInfo, PlayerInfo, TeamInfo

router = APIRouter()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class MarkPickedRequest(BaseModel):
    player_id: int


class SetPositionRequest(BaseModel):
    position: int  # 1-12, user's pick slot in round 1


class DraftOrderEntry(BaseModel):
    team_id: int
    position: int


class SetDraftOrderRequest(BaseModel):
    order: list[DraftOrderEntry]


class PlacePickRequest(BaseModel):
    player_id: int
    round: int
    draft_position: int  # 1-based team draft slot


# ---------------------------------------------------------------------------
# Standard endpoints
# ---------------------------------------------------------------------------

@router.get("/picks", response_model=list[DraftPickInfo])
async def get_draft_picks():
    """Get all draft picks with player and team details."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """
            SELECT
                dp.round, dp.pick_number, dp.overall_pick, dp.adp,
                p.id AS player_id, p.espn_id, p.full_name, p.position,
                p.nfl_team, p.status, p.injury_status,
                p.projected_points, p.ros_projection, p.composite_score,
                p.trade_value, p.boom_probability, p.bust_probability,
                p.sleeper_trending_add, p.sleeper_trending_drop, p.headshot_url,
                t.id AS team_id, t.espn_team_id, t.team_name, t.owner_name,
                t.wins, t.losses, t.ties, t.points_for, t.points_against,
                t.is_user_team, t.power_rank_score, t.playoff_probability
            FROM draft_pick dp
            JOIN player p ON p.id = dp.player_id
            JOIN team t ON t.id = dp.team_id
            ORDER BY dp.overall_pick ASC
            """
        )

        if not rows:
            return []

        return [
            DraftPickInfo(
                round=r["round"],
                pick_number=r["pick_number"],
                overall_pick=r["overall_pick"],
                adp=r["adp"],
                value_diff=round(r["adp"] - r["overall_pick"], 1) if r["adp"] else None,
                player=PlayerInfo(
                    id=r["player_id"], espn_id=r["espn_id"], full_name=r["full_name"],
                    position=r["position"], nfl_team=r["nfl_team"], status=r["status"],
                    injury_status=r["injury_status"],
                    projected_points=r["projected_points"] or 0,
                    ros_projection=r["ros_projection"] or 0,
                    composite_score=r["composite_score"] or 0,
                    trade_value=r["trade_value"] or 0,
                    boom_probability=r["boom_probability"] or 0,
                    bust_probability=r["bust_probability"] or 0,
                    sleeper_trending_add=r["sleeper_trending_add"] or 0,
                    sleeper_trending_drop=r["sleeper_trending_drop"] or 0,
                    headshot_url=r["headshot_url"],
                ),
                team=TeamInfo(
                    id=r["team_id"], espn_team_id=r["espn_team_id"],
                    team_name=r["team_name"], owner_name=r["owner_name"],
                    wins=r["wins"], losses=r["losses"], ties=r["ties"],
                    points_for=r["points_for"], points_against=r["points_against"],
                    is_user_team=bool(r["is_user_team"]),
                    power_rank_score=r["power_rank_score"],
                    playoff_probability=r["playoff_probability"],
                ),
            )
            for r in rows
        ]
    finally:
        await db.close()


@router.get("/value-tracker")
async def get_draft_value_tracker():
    """Analyze draft value: compare each pick's actual performance vs ADP."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """
            SELECT dp.round, dp.pick_number, dp.overall_pick, dp.adp,
                   p.id AS player_id, p.full_name, p.position, p.nfl_team,
                   p.composite_score, p.ros_projection,
                   t.id AS team_id, t.team_name, t.is_user_team
            FROM draft_pick dp
            JOIN player p ON p.id = dp.player_id
            JOIN team t ON t.id = dp.team_id
            ORDER BY dp.overall_pick ASC
            """
        )

        if not rows:
            return {"picks": [], "summary": {"total_value": 0, "best_pick": None, "worst_pick": None}}

        picks = []
        best_pick = None
        worst_pick = None
        user_total_value = 0
        user_pick_count = 0

        for r in rows:
            value_diff = round(r["adp"] - r["overall_pick"], 1) if r["adp"] else 0
            score = r["composite_score"] or 0
            if score >= 80:
                grade = "Elite"
            elif score >= 60:
                grade = "Strong"
            elif score >= 40:
                grade = "Average"
            elif score >= 20:
                grade = "Below Average"
            elif score > 0:
                grade = "Bust"
            else:
                grade = "N/A"

            pick_data = {
                "round": r["round"], "pick_number": r["pick_number"],
                "overall_pick": r["overall_pick"], "player_name": r["full_name"],
                "player_id": r["player_id"], "position": r["position"],
                "nfl_team": r["nfl_team"], "team_name": r["team_name"],
                "is_user_team": bool(r["is_user_team"]), "adp": r["adp"],
                "value_diff": value_diff, "composite_score": score,
                "performance_grade": grade,
            }
            picks.append(pick_data)

            if r["is_user_team"]:
                user_total_value += value_diff
                user_pick_count += 1
                if best_pick is None or value_diff > best_pick["value_diff"]:
                    best_pick = pick_data
                if worst_pick is None or value_diff < worst_pick["value_diff"]:
                    worst_pick = pick_data

        return {
            "picks": picks,
            "summary": {
                "total_value": round(user_total_value, 1),
                "avg_value_per_pick": (
                    round(user_total_value / user_pick_count, 1) if user_pick_count else 0
                ),
                "best_pick": best_pick,
                "worst_pick": worst_pick,
            },
        }
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Live draft: set user's draft position
# ---------------------------------------------------------------------------

@router.post("/set-my-position")
async def set_my_draft_position(body: SetPositionRequest):
    """Set user's draft position (1-based, e.g. 7 = 7th pick in round 1)."""
    db = await get_db()
    try:
        # Ensure draft_position column exists
        try:
            await db.execute("ALTER TABLE team ADD COLUMN draft_position INTEGER")
            await db.commit()
        except Exception:
            pass

        league_row = await db.execute_fetchall("SELECT id, num_teams FROM league LIMIT 1")
        if not league_row:
            raise HTTPException(status_code=404, detail="League not synced")

        num_teams = league_row[0]["num_teams"]
        if body.position < 1 or body.position > num_teams:
            raise HTTPException(
                status_code=400,
                detail=f"Position must be between 1 and {num_teams}"
            )

        league_id = league_row[0]["id"]

        # Set user team's draft position
        await db.execute(
            "UPDATE team SET draft_position = ? WHERE is_user_team = 1 AND league_id = ?",
            (body.position, league_id)
        )
        await db.commit()

        return {"status": "ok", "position": body.position, "num_teams": num_teams}
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Live draft: set full draft order for all teams
# ---------------------------------------------------------------------------

@router.post("/set-order")
async def set_draft_order(body: SetDraftOrderRequest):
    """Set draft order for all teams. Maps each team to a draft slot (1-N)."""
    db = await get_db()
    try:
        # Ensure draft_position column exists
        try:
            await db.execute("ALTER TABLE team ADD COLUMN draft_position INTEGER")
            await db.commit()
        except Exception:
            pass

        league_row = await db.execute_fetchall("SELECT id, num_teams FROM league LIMIT 1")
        if not league_row:
            raise HTTPException(status_code=404, detail="League not synced")
        league_id = league_row[0]["id"]
        num_teams = league_row[0]["num_teams"]

        # Validate
        if len(body.order) != num_teams:
            raise HTTPException(
                status_code=400,
                detail=f"Must provide exactly {num_teams} entries, got {len(body.order)}"
            )
        positions = [e.position for e in body.order]
        if sorted(positions) != list(range(1, num_teams + 1)):
            raise HTTPException(status_code=400, detail="Positions must be 1 through {num_teams} with no duplicates")

        team_ids = [e.team_id for e in body.order]
        teams = await db.execute_fetchall(
            "SELECT id FROM team WHERE league_id = ?", (league_id,)
        )
        valid_ids = {t["id"] for t in teams}
        for tid in team_ids:
            if tid not in valid_ids:
                raise HTTPException(status_code=400, detail=f"Team ID {tid} not found in league")

        # Update all teams
        for entry in body.order:
            await db.execute(
                "UPDATE team SET draft_position = ? WHERE id = ?",
                (entry.position, entry.team_id)
            )
        await db.commit()

        return {"status": "ok", "num_teams": num_teams}
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Live draft: available players (search)
# ---------------------------------------------------------------------------

@router.get("/available")
async def get_available_players(
    q: str = Query("", description="Search by player name"),
    position: str = Query("", description="Filter by position"),
    limit: int = Query(50, ge=1, le=200),
):
    """Get available (undrafted) players, optionally filtered by name/position."""
    db = await get_db()
    try:
        league_row = await db.execute_fetchall("SELECT id FROM league LIMIT 1")
        if not league_row:
            return []
        league_id = league_row[0]["id"]

        query = """
            SELECT id, full_name, position, nfl_team, projected_points,
                   ros_projection, headshot_url
            FROM player
            WHERE id NOT IN (SELECT player_id FROM draft_pick WHERE league_id = ?)
            AND position IN ('QB', 'RB', 'WR', 'TE', 'K', 'DST', 'D/ST')
        """
        params: list = [league_id]

        if q:
            query += " AND full_name LIKE ?"
            params.append(f"%{q}%")
        if position:
            query += " AND position = ?"
            params.append(position)

        query += " ORDER BY projected_points DESC LIMIT ?"
        params.append(limit)

        rows = await db.execute_fetchall(query, params)
        return [
            {
                "id": r["id"],
                "full_name": r["full_name"],
                "position": r["position"],
                "nfl_team": r["nfl_team"],
                "projected_points": round(r["projected_points"] or 0, 1),
                "headshot_url": r["headshot_url"],
            }
            for r in rows
        ]
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Live draft: mark a player as picked
# ---------------------------------------------------------------------------

@router.post("/mark-picked")
async def mark_player_picked(body: MarkPickedRequest):
    """Record a pick in a live draft. Tracks pick order and assigns to
    the user's team when it's their turn (snake draft)."""
    db = await get_db()
    try:
        league_row = await db.execute_fetchall("SELECT id, num_teams FROM league LIMIT 1")
        if not league_row:
            raise HTTPException(status_code=404, detail="League not synced")
        league_id = league_row[0]["id"]
        num_teams = league_row[0]["num_teams"]

        # Current pick count
        count_row = await db.execute_fetchall(
            "SELECT COUNT(*) as cnt FROM draft_pick WHERE league_id = ?",
            (league_id,)
        )
        current_count = count_row[0]["cnt"] if count_row else 0
        overall_pick = current_count + 1
        round_num = ((overall_pick - 1) // num_teams) + 1
        pick_in_round = ((overall_pick - 1) % num_teams) + 1

        # Snake draft position calculation
        pos_in_round = ((overall_pick - 1) % num_teams)
        if round_num % 2 == 0:
            pos_in_round = num_teams - 1 - pos_in_round
        current_draft_pos = pos_in_round + 1

        # Look up team by draft_position
        picking_team = await db.execute_fetchall(
            "SELECT id, team_name, is_user_team FROM team WHERE draft_position = ? AND league_id = ?",
            (current_draft_pos, league_id)
        )
        if picking_team:
            team_id = picking_team[0]["id"]
            team_name = picking_team[0]["team_name"]
            is_user_pick = bool(picking_team[0]["is_user_team"])
        else:
            # Fallback: draft order not set, assign to first non-user team
            other = await db.execute_fetchall(
                "SELECT id, team_name FROM team WHERE is_user_team = 0 AND league_id = ? LIMIT 1",
                (league_id,)
            )
            team_id = other[0]["id"] if other else 1
            team_name = other[0]["team_name"] if other else "Unknown"
            is_user_pick = False

        # Check player exists
        player_row = await db.execute_fetchall(
            "SELECT id, full_name, position FROM player WHERE id = ?",
            (body.player_id,)
        )
        if not player_row:
            raise HTTPException(status_code=404, detail="Player not found")

        # Check not already drafted
        already = await db.execute_fetchall(
            "SELECT id FROM draft_pick WHERE player_id = ? AND league_id = ?",
            (body.player_id, league_id)
        )
        if already:
            raise HTTPException(status_code=400, detail="Player already drafted")

        # Insert pick
        await db.execute("""
            INSERT INTO draft_pick (league_id, team_id, player_id, round, pick_number, overall_pick)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (league_id, team_id, body.player_id, round_num, pick_in_round, overall_pick))
        await db.commit()

        return {
            "status": "ok",
            "overall_pick": overall_pick,
            "round": round_num,
            "pick_in_round": pick_in_round,
            "player_name": player_row[0]["full_name"],
            "position": player_row[0]["position"],
            "is_user_pick": is_user_pick,
            "team_name": team_name,
        }
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Live draft: place a pick at a specific round + team slot (no shifting)
# ---------------------------------------------------------------------------

@router.post("/place-pick")
async def place_pick(body: PlacePickRequest):
    """Place a player at a specific round + draft_position slot.
    If the slot is already taken, the old pick is replaced (no shifting).
    Uses snake draft logic to compute overall_pick."""
    db = await get_db()
    try:
        league_row = await db.execute_fetchall("SELECT id, num_teams FROM league LIMIT 1")
        if not league_row:
            raise HTTPException(status_code=404, detail="League not synced")
        league_id = league_row[0]["id"]
        num_teams = league_row[0]["num_teams"]

        if body.round < 1:
            raise HTTPException(status_code=400, detail="Round must be >= 1")
        if body.draft_position < 1 or body.draft_position > num_teams:
            raise HTTPException(
                status_code=400,
                detail=f"draft_position must be 1-{num_teams}",
            )

        # Snake draft: compute overall_pick from round + draft_position
        if body.round % 2 == 1:
            # Odd round: normal order
            overall_pick = (body.round - 1) * num_teams + body.draft_position
        else:
            # Even round: reversed (snake)
            overall_pick = (body.round - 1) * num_teams + (num_teams - body.draft_position + 1)

        pick_in_round = ((overall_pick - 1) % num_teams) + 1

        # Look up the team at this draft_position
        picking_team = await db.execute_fetchall(
            "SELECT id, team_name, is_user_team FROM team WHERE draft_position = ? AND league_id = ?",
            (body.draft_position, league_id),
        )
        if not picking_team:
            raise HTTPException(
                status_code=400,
                detail=f"No team found at draft position {body.draft_position}",
            )
        team_id = picking_team[0]["id"]
        team_name = picking_team[0]["team_name"]

        # Check player exists
        player_row = await db.execute_fetchall(
            "SELECT id, full_name, position FROM player WHERE id = ?",
            (body.player_id,),
        )
        if not player_row:
            raise HTTPException(status_code=404, detail="Player not found")

        # If this player is already drafted elsewhere, remove that pick first
        existing_player = await db.execute_fetchall(
            "SELECT id, overall_pick FROM draft_pick WHERE player_id = ? AND league_id = ?",
            (body.player_id, league_id),
        )
        if existing_player:
            await db.execute(
                "DELETE FROM draft_pick WHERE id = ?",
                (existing_player[0]["id"],),
            )

        # Check if a pick already exists at this slot
        replaced_player = None
        existing_slot = await db.execute_fetchall(
            "SELECT dp.id, p.full_name FROM draft_pick dp JOIN player p ON dp.player_id = p.id WHERE dp.overall_pick = ? AND dp.league_id = ?",
            (overall_pick, league_id),
        )
        if existing_slot:
            replaced_player = existing_slot[0]["full_name"]
            await db.execute(
                "DELETE FROM draft_pick WHERE id = ?",
                (existing_slot[0]["id"],),
            )

        # Insert the new pick
        await db.execute(
            """
            INSERT INTO draft_pick (league_id, team_id, player_id, round, pick_number, overall_pick)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (league_id, team_id, body.player_id, body.round, pick_in_round, overall_pick),
        )
        await db.commit()

        result = {
            "status": "ok",
            "player_name": player_row[0]["full_name"],
            "overall_pick": overall_pick,
            "round": body.round,
            "draft_position": body.draft_position,
            "team_name": team_name,
        }
        if replaced_player:
            result["replaced_player"] = replaced_player
        return result
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Live draft: insert a pick at a specific slot, shifting others up
# ---------------------------------------------------------------------------

class InsertPickRequest(BaseModel):
    player_id: int
    overall_pick: int
    team_id: int


@router.post("/insert-pick")
async def insert_pick_at_position(body: InsertPickRequest):
    """Insert a pick at a specific overall_pick, shifting later picks up by 1."""
    db = await get_db()
    try:
        league_row = await db.execute_fetchall("SELECT id, num_teams FROM league LIMIT 1")
        if not league_row:
            raise HTTPException(status_code=404, detail="League not synced")
        league_id = league_row[0]["id"]
        num_teams = league_row[0]["num_teams"]

        # Verify player exists and is not drafted
        player_row = await db.execute_fetchall(
            "SELECT id, full_name FROM player WHERE id = ?", (body.player_id,)
        )
        if not player_row:
            raise HTTPException(status_code=404, detail="Player not found")
        already = await db.execute_fetchall(
            "SELECT id FROM draft_pick WHERE player_id = ? AND league_id = ?",
            (body.player_id, league_id)
        )
        if already:
            raise HTTPException(status_code=400, detail="Player already drafted")

        # Shift all picks at or after the target slot UP by 1
        later_picks = await db.execute_fetchall("""
            SELECT dp.id, dp.overall_pick
            FROM draft_pick dp
            WHERE dp.league_id = ? AND dp.overall_pick >= ?
            ORDER BY dp.overall_pick DESC
        """, (league_id, body.overall_pick))

        teams_by_pos = {}
        all_teams = await db.execute_fetchall(
            "SELECT id, draft_position FROM team WHERE league_id = ? AND draft_position IS NOT NULL",
            (league_id,)
        )
        for t in all_teams:
            teams_by_pos[t["draft_position"]] = t["id"]

        for row in later_picks:
            new_overall = row["overall_pick"] + 1
            new_round = ((new_overall - 1) // num_teams) + 1
            new_pick_in_round = ((new_overall - 1) % num_teams) + 1
            pos_in_round = (new_overall - 1) % num_teams
            if new_round % 2 == 0:
                pos_in_round = num_teams - 1 - pos_in_round
            draft_pos = pos_in_round + 1
            new_team_id = teams_by_pos.get(draft_pos)
            if new_team_id:
                await db.execute("""
                    UPDATE draft_pick
                    SET overall_pick = ?, round = ?, pick_number = ?, team_id = ?
                    WHERE id = ?
                """, (new_overall, new_round, new_pick_in_round, new_team_id, row["id"]))
            else:
                await db.execute("""
                    UPDATE draft_pick
                    SET overall_pick = ?, round = ?, pick_number = ?
                    WHERE id = ?
                """, (new_overall, new_round, new_pick_in_round, row["id"]))

        # Insert the new pick at the target slot
        target_round = ((body.overall_pick - 1) // num_teams) + 1
        target_pick_in_round = ((body.overall_pick - 1) % num_teams) + 1
        await db.execute("""
            INSERT INTO draft_pick (league_id, team_id, player_id, round, pick_number, overall_pick)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (league_id, body.team_id, body.player_id, target_round, target_pick_in_round, body.overall_pick))

        await db.commit()

        return {
            "status": "ok",
            "inserted_player": player_row[0]["full_name"],
            "overall_pick": body.overall_pick,
            "picks_shifted": len(later_picks),
        }
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Live draft: remove a specific pick (by overall_pick number)
# ---------------------------------------------------------------------------

@router.delete("/remove-pick/{overall_pick}")
async def remove_specific_pick(overall_pick: int):
    """Remove a specific draft pick and shift all subsequent picks down by 1."""
    db = await get_db()
    try:
        league_row = await db.execute_fetchall("SELECT id, num_teams FROM league LIMIT 1")
        if not league_row:
            raise HTTPException(status_code=404, detail="League not synced")
        league_id = league_row[0]["id"]
        num_teams = league_row[0]["num_teams"]

        # Find the pick to remove
        pick_row = await db.execute_fetchall("""
            SELECT dp.id, p.full_name
            FROM draft_pick dp
            JOIN player p ON p.id = dp.player_id
            WHERE dp.league_id = ? AND dp.overall_pick = ?
        """, (league_id, overall_pick))
        if not pick_row:
            raise HTTPException(status_code=404, detail=f"No pick found at overall_pick {overall_pick}")

        removed_player = pick_row[0]["full_name"]

        # Delete the pick
        await db.execute("DELETE FROM draft_pick WHERE id = ?", (pick_row[0]["id"],))

        # Get all picks that need to shift down (those after the removed pick)
        later_picks = await db.execute_fetchall("""
            SELECT dp.id, dp.overall_pick
            FROM draft_pick dp
            WHERE dp.league_id = ? AND dp.overall_pick > ?
            ORDER BY dp.overall_pick ASC
        """, (league_id, overall_pick))

        # Load draft order for snake recalculation
        teams_by_pos = {}
        all_teams = await db.execute_fetchall(
            "SELECT id, draft_position FROM team WHERE league_id = ? AND draft_position IS NOT NULL",
            (league_id,)
        )
        for t in all_teams:
            teams_by_pos[t["draft_position"]] = t["id"]

        # Shift each later pick down by 1 and reassign team via snake
        picks_shifted = 0
        for row in later_picks:
            new_overall = row["overall_pick"] - 1
            new_round = ((new_overall - 1) // num_teams) + 1
            new_pick_in_round = ((new_overall - 1) % num_teams) + 1

            # Snake draft team assignment
            pos_in_round = (new_overall - 1) % num_teams
            if new_round % 2 == 0:
                pos_in_round = num_teams - 1 - pos_in_round
            draft_pos = pos_in_round + 1
            new_team_id = teams_by_pos.get(draft_pos)

            if new_team_id:
                await db.execute("""
                    UPDATE draft_pick
                    SET overall_pick = ?, round = ?, pick_number = ?, team_id = ?
                    WHERE id = ?
                """, (new_overall, new_round, new_pick_in_round, new_team_id, row["id"]))
            else:
                await db.execute("""
                    UPDATE draft_pick
                    SET overall_pick = ?, round = ?, pick_number = ?
                    WHERE id = ?
                """, (new_overall, new_round, new_pick_in_round, row["id"]))
            picks_shifted += 1

        await db.commit()

        return {
            "status": "ok",
            "removed_player": removed_player,
            "picks_shifted": picks_shifted,
        }
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Live draft: undo last pick
# ---------------------------------------------------------------------------

@router.delete("/undo-last")
async def undo_last_pick():
    """Remove the last draft pick (undo a mistake)."""
    db = await get_db()
    try:
        league_row = await db.execute_fetchall("SELECT id FROM league LIMIT 1")
        if not league_row:
            raise HTTPException(status_code=404, detail="League not synced")
        league_id = league_row[0]["id"]

        last_pick = await db.execute_fetchall("""
            SELECT dp.id, p.full_name
            FROM draft_pick dp
            JOIN player p ON p.id = dp.player_id
            WHERE dp.league_id = ?
            ORDER BY dp.overall_pick DESC LIMIT 1
        """, (league_id,))

        if not last_pick:
            raise HTTPException(status_code=404, detail="No picks to undo")

        await db.execute("DELETE FROM draft_pick WHERE id = ?", (last_pick[0]["id"],))
        await db.commit()

        return {"status": "ok", "undone": last_pick[0]["full_name"]}
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Live draft: current state (lightweight)
# ---------------------------------------------------------------------------

@router.get("/live-state")
async def get_live_state():
    """Get current live draft state: pick count, user's turn, user roster."""
    db = await get_db()
    try:
        # Ensure draft_position column exists
        try:
            await db.execute("ALTER TABLE team ADD COLUMN draft_position INTEGER")
            await db.commit()
        except Exception:
            pass

        league_row = await db.execute_fetchall("SELECT id, num_teams FROM league LIMIT 1")
        if not league_row:
            return {"picks_made": 0, "total": 0}
        league_id = league_row[0]["id"]
        num_teams = league_row[0]["num_teams"]
        total = num_teams * 16

        count_row = await db.execute_fetchall(
            "SELECT COUNT(*) as cnt FROM draft_pick WHERE league_id = ?",
            (league_id,)
        )
        picks_made = count_row[0]["cnt"] if count_row else 0
        overall_pick = picks_made + 1

        # Draft order (all teams)
        all_teams = await db.execute_fetchall(
            "SELECT id, team_name, owner_name, is_user_team, draft_position FROM team WHERE league_id = ? ORDER BY draft_position ASC",
            (league_id,)
        )
        draft_order = [
            {
                "team_id": t["id"],
                "team_name": t["team_name"],
                "owner_name": t["owner_name"] or "",
                "draft_position": t["draft_position"],
                "is_user_team": bool(t["is_user_team"]),
            }
            for t in all_teams
            if t["draft_position"] is not None
        ]
        draft_order_set = len(draft_order) > 0

        # User team info
        user_team = [t for t in all_teams if t["is_user_team"]]
        user_team_id = user_team[0]["id"] if user_team else None
        user_draft_pos = None
        try:
            user_draft_pos = user_team[0]["draft_position"] if user_team else None
        except (IndexError, KeyError):
            pass

        # Current picking team (snake draft)
        is_user_turn = False
        user_next_pick = None
        current_team = None
        round_num = ((overall_pick - 1) // num_teams) + 1

        if draft_order_set and picks_made < total:
            pos_in_round = ((overall_pick - 1) % num_teams)
            if round_num % 2 == 0:
                pos_in_round = num_teams - 1 - pos_in_round
            current_draft_pos = pos_in_round + 1

            # Find the team picking now
            for t in all_teams:
                if t["draft_position"] == current_draft_pos:
                    current_team = {
                        "team_id": t["id"],
                        "team_name": t["team_name"],
                        "owner_name": t["owner_name"] or "",
                        "is_user_team": bool(t["is_user_team"]),
                    }
                    break

            if user_draft_pos:
                is_user_turn = current_draft_pos == user_draft_pos

                # Find user's next pick
                for pn in range(overall_pick, total + 1):
                    r = ((pn - 1) // num_teams) + 1
                    p = ((pn - 1) % num_teams)
                    if r % 2 == 0:
                        p = num_teams - 1 - p
                    if (p + 1) == user_draft_pos:
                        user_next_pick = pn
                        break

        # User's drafted players
        user_roster = []
        if user_team_id:
            roster_rows = await db.execute_fetchall("""
                SELECT p.full_name, p.position, p.nfl_team, p.projected_points,
                       dp.overall_pick, dp.round
                FROM draft_pick dp
                JOIN player p ON p.id = dp.player_id
                WHERE dp.team_id = ? AND dp.league_id = ?
                ORDER BY dp.overall_pick
            """, (user_team_id, league_id))
            user_roster = [
                {
                    "full_name": r["full_name"],
                    "position": r["position"],
                    "nfl_team": r["nfl_team"],
                    "projected_points": round(r["projected_points"] or 0, 1),
                    "round": r["round"],
                    "overall_pick": r["overall_pick"],
                }
                for r in roster_rows
            ]

        # All team rosters
        all_rosters: dict[int, list] = {}
        if draft_order_set:
            all_roster_rows = await db.execute_fetchall("""
                SELECT dp.team_id, p.full_name, p.position, p.nfl_team,
                       p.projected_points, dp.round, dp.overall_pick
                FROM draft_pick dp
                JOIN player p ON p.id = dp.player_id
                WHERE dp.league_id = ?
                ORDER BY dp.overall_pick
            """, (league_id,))
            for r in all_roster_rows:
                tid = r["team_id"]
                if tid not in all_rosters:
                    all_rosters[tid] = []
                all_rosters[tid].append({
                    "full_name": r["full_name"],
                    "position": r["position"],
                    "nfl_team": r["nfl_team"],
                    "projected_points": round(r["projected_points"] or 0, 1),
                    "round": r["round"],
                    "overall_pick": r["overall_pick"],
                })

        # Recent picks (last 5)
        recent = await db.execute_fetchall("""
            SELECT p.full_name, p.position, dp.overall_pick, dp.round,
                   t.is_user_team, t.team_name
            FROM draft_pick dp
            JOIN player p ON p.id = dp.player_id
            JOIN team t ON t.id = dp.team_id
            WHERE dp.league_id = ?
            ORDER BY dp.overall_pick DESC LIMIT 5
        """, (league_id,))
        recent_picks = [
            {
                "full_name": r["full_name"],
                "position": r["position"],
                "overall_pick": r["overall_pick"],
                "round": r["round"],
                "is_user_pick": bool(r["is_user_team"]),
                "team_name": r["team_name"],
            }
            for r in recent
        ]

        return {
            "picks_made": picks_made,
            "total": total,
            "current_pick": overall_pick if picks_made < total else None,
            "current_round": round_num if picks_made < total else None,
            "is_user_turn": is_user_turn,
            "user_next_pick": user_next_pick,
            "user_draft_position": user_draft_pos,
            "is_complete": picks_made >= total,
            "user_roster": user_roster,
            "recent_picks": recent_picks,
            "draft_order": draft_order,
            "draft_order_set": draft_order_set,
            "current_team": current_team,
            "all_rosters": all_rosters,
        }
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Draft suggestions (top 3 picks for user)
# ---------------------------------------------------------------------------

ROSTER_NEEDS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "K": 1, "DST": 1}
TOTAL_ROSTER = 16


@router.get("/suggestions")
async def get_draft_suggestions():
    """Get top 3 suggested picks based on team needs and best available."""
    db = await get_db()
    try:
        league_row = await db.execute_fetchall("SELECT id, num_teams FROM league LIMIT 1")
        if not league_row:
            return {"suggestions": [], "message": "League not synced"}
        league_id = league_row[0]["id"]

        team_row = await db.execute_fetchall(
            "SELECT id FROM team WHERE is_user_team = 1 AND league_id = ?",
            (league_id,)
        )
        if not team_row:
            return {"suggestions": [], "message": "User team not set"}
        user_team_id = team_row[0]["id"]

        user_picks = await db.execute_fetchall("""
            SELECT p.position FROM draft_pick dp
            JOIN player p ON p.id = dp.player_id
            WHERE dp.team_id = ? AND dp.league_id = ?
        """, (user_team_id, league_id))

        pos_count: dict[str, int] = {}
        for p in user_picks:
            pos = p["position"]
            pos_count[pos] = pos_count.get(pos, 0) + 1
        picks_made = len(user_picks)

        # Position need scores
        need_scores: dict[str, float] = {}
        for pos, required in ROSTER_NEEDS.items():
            if pos == "FLEX":
                continue
            have = pos_count.get(pos, 0)
            starter_need = max(0, required - have)
            ideal = required + (3 if pos in ("RB", "WR") else 1 if pos in ("QB", "TE") else 0)
            depth_need = max(0, ideal - have)
            need_scores[pos] = starter_need * 3 + depth_need

        if picks_made >= TOTAL_ROSTER - 3:
            if pos_count.get("K", 0) == 0:
                need_scores["K"] = 10
            if pos_count.get("DST", 0) == 0 and pos_count.get("D/ST", 0) == 0:
                need_scores["DST"] = 10
                need_scores["D/ST"] = 10

        available = await db.execute_fetchall("""
            SELECT id, full_name, position, nfl_team, projected_points,
                   ros_projection, composite_score, headshot_url
            FROM player
            WHERE id NOT IN (SELECT player_id FROM draft_pick WHERE league_id = ?)
            AND position IN ('QB', 'RB', 'WR', 'TE', 'K', 'DST', 'D/ST')
            ORDER BY projected_points DESC
            LIMIT 200
        """, (league_id,))

        if not available:
            return {"suggestions": [], "message": "No available players. Click 'Load Players' first."}

        scored = []
        for p in available:
            pos = p["position"]
            need = need_scores.get(pos, 0.5)
            proj = p["projected_points"] or 0
            quality = max(proj, (p["ros_projection"] or 0), (p["composite_score"] or 0) / 10)
            score = need * 2 + quality
            scored.append({
                "id": p["id"], "full_name": p["full_name"], "position": pos,
                "nfl_team": p["nfl_team"],
                "projected_points": round(proj, 1),
                "headshot_url": p["headshot_url"],
                "need_score": need, "pick_score": round(score, 1),
                "reason": _suggestion_reason(pos, need, proj, picks_made),
            })

        scored.sort(key=lambda x: x["pick_score"], reverse=True)
        suggestions: list[dict] = []
        used_positions: set[str] = set()
        for s in scored:
            if len(suggestions) >= 3:
                break
            if s["position"] in used_positions and len(suggestions) < 2:
                continue
            suggestions.append(s)
            used_positions.add(s["position"])
        if len(suggestions) < 3:
            for s in scored:
                if len(suggestions) >= 3:
                    break
                if s not in suggestions:
                    suggestions.append(s)

        return {
            "suggestions": suggestions,
            "picks_made": picks_made,
            "total_roster": TOTAL_ROSTER,
            "position_counts": pos_count,
        }
    finally:
        await db.close()


def _suggestion_reason(position: str, need: float, projected: float, picks_made: int) -> str:
    if need >= 3:
        return f"You need a starting {position}. High priority pick."
    elif need >= 1:
        return f"Adds depth at {position}. Projected {projected:.1f} pts/week."
    elif picks_made < 6:
        return f"Best player available. Elite {position} talent."
    else:
        return f"Strong value pick at {position}. Projected {projected:.1f} pts/week."


# ---------------------------------------------------------------------------
# Refresh / load players from ESPN
# ---------------------------------------------------------------------------

@router.post("/refresh")
async def refresh_draft_data():
    """Load/refresh player pool from ESPN. Call before draft to populate available players."""
    import logging
    logger = logging.getLogger(__name__)

    try:
        from ..adapters.espn_adapter import get_league, get_draft_results, get_free_agents, get_rosters
        league = get_league()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to ESPN: {str(e)}")

    db = await get_db()
    try:
        league_row = await db.execute_fetchall("SELECT id FROM league LIMIT 1")
        if not league_row:
            raise HTTPException(status_code=404, detail="League not synced")
        league_id = league_row[0]["id"]

        # Sync any ESPN draft picks
        new_picks = 0
        try:
            draft_picks = get_draft_results(league)
            for pick in draft_picks:
                espn_player_id = pick.get("espn_player_id")
                espn_team_id = pick.get("team_id")
                if not espn_player_id or not espn_team_id:
                    continue
                cursor = await db.execute(
                    "SELECT id FROM player WHERE espn_id = ?", (espn_player_id,)
                )
                p_row = await cursor.fetchone()
                if not p_row:
                    await db.execute(
                        "INSERT OR IGNORE INTO player (espn_id, full_name, position) VALUES (?, ?, ?)",
                        (espn_player_id, pick.get("player_name", "Unknown"), "??"),
                    )
                    cursor = await db.execute("SELECT id FROM player WHERE espn_id = ?", (espn_player_id,))
                    p_row = await cursor.fetchone()
                if not p_row:
                    continue
                cursor = await db.execute(
                    "SELECT id FROM team WHERE espn_team_id = ? AND league_id = ?",
                    (espn_team_id, league_id),
                )
                t_row = await cursor.fetchone()
                if not t_row:
                    continue
                result = await db.execute(
                    "INSERT OR IGNORE INTO draft_pick (league_id, team_id, player_id, round, pick_number, overall_pick) VALUES (?, ?, ?, ?, ?, ?)",
                    (league_id, t_row["id"], p_row["id"], pick["round"], pick["pick_number"], pick["overall_pick"]),
                )
                if result.rowcount and result.rowcount > 0:
                    new_picks += 1
            await db.commit()
        except Exception as e:
            logger.warning("Could not sync draft picks: %s", e)

        # Load free agents by position for comprehensive coverage
        fa_count = 0
        for pos in ["QB", "RB", "WR", "TE", "K", "D/ST"]:
            try:
                fas = get_free_agents(league, position=pos, limit=150)
                for fa in fas:
                    proj = fa.get("projected_points", 0)
                    if fa_count < 5:
                        logger.info("Sample player: %s (%s) - projected_points=%.1f",
                                    fa["full_name"], fa["position"], proj)
                    await db.execute("""
                        INSERT INTO player (espn_id, full_name, position, nfl_team, status,
                                            injury_status, projected_points)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(espn_id) DO UPDATE SET
                            full_name=excluded.full_name, position=excluded.position,
                            nfl_team=excluded.nfl_team, projected_points=excluded.projected_points,
                            updated_at=CURRENT_TIMESTAMP
                    """, (
                        fa["espn_id"], fa["full_name"], fa["position"],
                        fa.get("nfl_team"), fa.get("status"),
                        fa.get("injury_status"), proj,
                    ))
                fa_count += len(fas)
            except Exception as e:
                logger.warning("Could not fetch %s free agents: %s", pos, e)
        await db.commit()

        # Sync rosters for player details
        try:
            rosters = get_rosters(league)
            for espn_tid, players in rosters.items():
                for player in players:
                    await db.execute("""
                        INSERT INTO player (espn_id, full_name, position, nfl_team, status,
                                            injury_status, projected_points, headshot_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(espn_id) DO UPDATE SET
                            full_name=excluded.full_name, position=excluded.position,
                            nfl_team=excluded.nfl_team, status=excluded.status,
                            projected_points=excluded.projected_points,
                            headshot_url=excluded.headshot_url,
                            updated_at=CURRENT_TIMESTAMP
                    """, (
                        player["espn_id"], player["full_name"], player["position"],
                        player.get("nfl_team"), player.get("status"),
                        player.get("injury_status"), player.get("projected_points", 0),
                        player.get("headshot_url"),
                    ))
            await db.commit()
        except Exception as e:
            logger.warning("Could not sync rosters: %s", e)

        total_players = await db.execute_fetchall(
            "SELECT COUNT(*) as cnt FROM player WHERE position IN ('QB','RB','WR','TE','K','DST','D/ST')"
        )

        return {
            "status": "ok",
            "new_picks": new_picks,
            "players_loaded": total_players[0]["cnt"] if total_players else 0,
            "free_agents_fetched": fa_count,
        }
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Board (kept for compatibility but less useful in manual mode)
# ---------------------------------------------------------------------------

@router.get("/board")
async def get_draft_board():
    """Get the full draft board state."""
    db = await get_db()
    try:
        league_row = await db.execute_fetchall("SELECT * FROM league LIMIT 1")
        if not league_row:
            raise HTTPException(status_code=404, detail="League not synced yet")
        lr = league_row[0]
        num_teams = lr["num_teams"]

        teams = await db.execute_fetchall(
            "SELECT id, espn_team_id, team_name, owner_name, is_user_team FROM team WHERE league_id = ? ORDER BY espn_team_id",
            (lr["id"],),
        )
        picks = await db.execute_fetchall("""
            SELECT dp.round, dp.pick_number, dp.overall_pick,
                   p.full_name, p.position, p.nfl_team, p.projected_points,
                   t.espn_team_id, t.team_name, t.is_user_team
            FROM draft_pick dp
            JOIN player p ON p.id = dp.player_id
            JOIN team t ON t.id = dp.team_id
            WHERE dp.league_id = ?
            ORDER BY dp.overall_pick ASC
        """, (lr["id"],))

        total_picks = len(picks)
        expected_total = num_teams * 16

        return {
            "num_teams": num_teams,
            "total_rounds": 16,
            "picks_made": total_picks,
            "expected_total": expected_total,
            "is_active": 0 < total_picks < expected_total,
            "is_complete": total_picks >= expected_total,
            "current_pick": total_picks + 1 if total_picks < expected_total else None,
            "teams": [{"id": t["id"], "espn_team_id": t["espn_team_id"], "team_name": t["team_name"], "is_user_team": bool(t["is_user_team"]), "draft_position": None} for t in teams],
            "picks": [{"round": p["round"], "pick_number": p["pick_number"], "overall_pick": p["overall_pick"], "player_name": p["full_name"], "position": p["position"], "nfl_team": p["nfl_team"], "projected_points": p["projected_points"] or 0, "espn_team_id": p["espn_team_id"], "team_name": p["team_name"], "is_user_team": bool(p["is_user_team"])} for p in picks],
            "current_team_espn_id": None, "is_user_turn": False, "user_next_pick": None, "user_draft_position": None,
        }
    finally:
        await db.close()
