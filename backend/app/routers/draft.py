from fastapi import APIRouter, HTTPException
from ..database import get_db
from ..schemas.models import DraftPickInfo, PlayerInfo, TeamInfo

router = APIRouter()


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
                    id=r["player_id"],
                    espn_id=r["espn_id"],
                    full_name=r["full_name"],
                    position=r["position"],
                    nfl_team=r["nfl_team"],
                    status=r["status"],
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
                    id=r["team_id"],
                    espn_team_id=r["espn_team_id"],
                    team_name=r["team_name"],
                    owner_name=r["owner_name"],
                    wins=r["wins"],
                    losses=r["losses"],
                    ties=r["ties"],
                    points_for=r["points_for"],
                    points_against=r["points_against"],
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
            SELECT
                dp.round, dp.pick_number, dp.overall_pick, dp.adp,
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
                performance_grade = "Elite"
            elif score >= 60:
                performance_grade = "Strong"
            elif score >= 40:
                performance_grade = "Average"
            elif score >= 20:
                performance_grade = "Below Average"
            elif score > 0:
                performance_grade = "Bust"
            else:
                performance_grade = "N/A"

            pick_data = {
                "round": r["round"],
                "pick_number": r["pick_number"],
                "overall_pick": r["overall_pick"],
                "player_name": r["full_name"],
                "player_id": r["player_id"],
                "position": r["position"],
                "nfl_team": r["nfl_team"],
                "team_name": r["team_name"],
                "is_user_team": bool(r["is_user_team"]),
                "adp": r["adp"],
                "value_diff": value_diff,
                "composite_score": score,
                "performance_grade": performance_grade,
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
# Live draft board
# ---------------------------------------------------------------------------

@router.get("/board")
async def get_draft_board():
    """Get the full draft board state for the live tracker."""
    db = await get_db()
    try:
        # League info
        league_row = await db.execute_fetchall("SELECT * FROM league LIMIT 1")
        if not league_row:
            raise HTTPException(status_code=404, detail="League not synced yet")
        lr = league_row[0]
        num_teams = lr["num_teams"]

        # All teams
        teams = await db.execute_fetchall(
            """SELECT id, espn_team_id, team_name, owner_name, is_user_team
               FROM team WHERE league_id = ?
               ORDER BY espn_team_id""",
            (lr["id"],)
        )

        # All draft picks
        picks = await db.execute_fetchall("""
            SELECT dp.round, dp.pick_number, dp.overall_pick,
                   p.full_name, p.position, p.nfl_team, p.projected_points,
                   p.headshot_url, p.espn_id AS player_espn_id,
                   t.espn_team_id, t.team_name, t.is_user_team
            FROM draft_pick dp
            JOIN player p ON p.id = dp.player_id
            JOIN team t ON t.id = dp.team_id
            WHERE dp.league_id = ?
            ORDER BY dp.overall_pick ASC
        """, (lr["id"],))

        total_picks = len(picks)
        total_rounds = 16  # Standard fantasy draft
        expected_total = num_teams * total_rounds

        # Determine draft order from round 1 picks
        draft_order = []
        for p in picks:
            if p["round"] == 1:
                draft_order.append(p["espn_team_id"])

        # Find user's draft position (1-based)
        user_espn_id = None
        for t in teams:
            if t["is_user_team"]:
                user_espn_id = t["espn_team_id"]
                break

        user_draft_position = None
        if user_espn_id and draft_order:
            try:
                user_draft_position = draft_order.index(user_espn_id) + 1
            except ValueError:
                pass

        # Calculate current pick and whose turn it is
        is_active = 0 < total_picks < expected_total
        is_complete = total_picks >= expected_total
        current_pick = total_picks + 1 if is_active else None

        # Determine who picks at current_pick (snake draft)
        current_team_espn_id = None
        is_user_turn = False
        user_next_pick = None

        if current_pick and draft_order:
            round_num = ((current_pick - 1) // num_teams) + 1
            pos_in_round = ((current_pick - 1) % num_teams)
            # Snake: even rounds are reversed
            if round_num % 2 == 0:
                pos_in_round = num_teams - 1 - pos_in_round
            if pos_in_round < len(draft_order):
                current_team_espn_id = draft_order[pos_in_round]
                is_user_turn = current_team_espn_id == user_espn_id

        # Calculate user's next pick
        if user_draft_position and draft_order and current_pick:
            for pick_num in range(current_pick, expected_total + 1):
                r = ((pick_num - 1) // num_teams) + 1
                p = ((pick_num - 1) % num_teams)
                if r % 2 == 0:
                    p = num_teams - 1 - p
                if p < len(draft_order) and draft_order[p] == user_espn_id:
                    user_next_pick = pick_num
                    break

        # Build team list with draft order position
        team_list = []
        for t in teams:
            order_pos = None
            if t["espn_team_id"] in draft_order:
                order_pos = draft_order.index(t["espn_team_id"]) + 1
            team_list.append({
                "id": t["id"],
                "espn_team_id": t["espn_team_id"],
                "team_name": t["team_name"],
                "owner_name": t["owner_name"],
                "is_user_team": bool(t["is_user_team"]),
                "draft_position": order_pos,
            })
        # Sort by draft position
        team_list.sort(key=lambda x: x["draft_position"] or 999)

        # Build picks list
        pick_list = [
            {
                "round": p["round"],
                "pick_number": p["pick_number"],
                "overall_pick": p["overall_pick"],
                "player_name": p["full_name"],
                "position": p["position"],
                "nfl_team": p["nfl_team"],
                "projected_points": p["projected_points"] or 0,
                "espn_team_id": p["espn_team_id"],
                "team_name": p["team_name"],
                "is_user_team": bool(p["is_user_team"]),
            }
            for p in picks
        ]

        return {
            "num_teams": num_teams,
            "total_rounds": total_rounds,
            "picks_made": total_picks,
            "expected_total": expected_total,
            "is_active": is_active,
            "is_complete": is_complete,
            "current_pick": current_pick,
            "current_team_espn_id": current_team_espn_id,
            "is_user_turn": is_user_turn,
            "user_next_pick": user_next_pick,
            "user_draft_position": user_draft_position,
            "teams": team_list,
            "picks": pick_list,
        }
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Draft suggestions (top 3 picks for user)
# ---------------------------------------------------------------------------

# Standard roster needs for a fantasy team
ROSTER_NEEDS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "K": 1, "DST": 1}
FLEX_ELIGIBLE = {"RB", "WR", "TE"}
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

        # Get user team
        team_row = await db.execute_fetchall(
            "SELECT id FROM team WHERE is_user_team = 1 AND league_id = ?",
            (league_id,)
        )
        if not team_row:
            return {"suggestions": [], "message": "User team not set"}

        user_team_id = team_row[0]["id"]

        # Get user's drafted players and their positions
        user_picks = await db.execute_fetchall("""
            SELECT p.position FROM draft_pick dp
            JOIN player p ON p.id = dp.player_id
            WHERE dp.team_id = ? AND dp.league_id = ?
        """, (user_team_id, league_id))

        # Count positions already drafted
        pos_count = {}
        for p in user_picks:
            pos = p["position"]
            pos_count[pos] = pos_count.get(pos, 0) + 1

        picks_made = len(user_picks)

        # Calculate position need scores
        # Higher score = more needed
        need_scores = {}
        for pos, required in ROSTER_NEEDS.items():
            if pos == "FLEX":
                continue  # FLEX is filled by RB/WR/TE
            have = pos_count.get(pos, 0)
            starter_need = max(0, required - have)
            # Add bench depth value
            if pos in ("RB", "WR"):
                ideal = required + 3  # Want depth at RB/WR
            elif pos in ("QB", "TE"):
                ideal = required + 1
            else:
                ideal = required
            depth_need = max(0, ideal - have)
            need_scores[pos] = starter_need * 3 + depth_need

        # Late round strategy: prioritize K/DST if not yet drafted
        if picks_made >= TOTAL_ROSTER - 3:
            if pos_count.get("K", 0) == 0:
                need_scores["K"] = 10
            if pos_count.get("DST", 0) == 0 and pos_count.get("D/ST", 0) == 0:
                need_scores["DST"] = 10
                need_scores["D/ST"] = 10

        # Get all drafted player IDs
        all_drafted = await db.execute_fetchall(
            "SELECT player_id FROM draft_pick WHERE league_id = ?",
            (league_id,)
        )
        drafted_ids = {r["player_id"] for r in all_drafted}

        # Get available players (not drafted, in our DB)
        available = await db.execute_fetchall("""
            SELECT id, full_name, position, nfl_team, projected_points,
                   ros_projection, composite_score, headshot_url
            FROM player
            WHERE id NOT IN (
                SELECT player_id FROM draft_pick WHERE league_id = ?
            )
            AND position IN ('QB', 'RB', 'WR', 'TE', 'K', 'DST', 'D/ST')
            ORDER BY projected_points DESC
            LIMIT 200
        """, (league_id,))

        if not available:
            return {"suggestions": [], "message": "No available players found. Try refreshing draft data."}

        # Score each available player
        scored = []
        for p in available:
            pos = p["position"]
            need = need_scores.get(pos, 0.5)  # Base value for unknown positions
            proj = p["projected_points"] or 0
            ros = p["ros_projection"] or 0
            composite = p["composite_score"] or 0

            # Combined score: position need weight * player quality
            quality = max(proj, ros, composite / 10)
            score = need * 2 + quality

            scored.append({
                "id": p["id"],
                "full_name": p["full_name"],
                "position": pos,
                "nfl_team": p["nfl_team"],
                "projected_points": round(proj, 1),
                "headshot_url": p["headshot_url"],
                "need_score": need,
                "pick_score": round(score, 1),
                "reason": _suggestion_reason(pos, need, proj, picks_made),
            })

        # Sort by score, take top 3 with position diversity
        scored.sort(key=lambda x: x["pick_score"], reverse=True)
        suggestions = []
        used_positions = set()
        for s in scored:
            if len(suggestions) >= 3:
                break
            # Prefer position diversity in suggestions
            if s["position"] in used_positions and len(suggestions) < 2:
                continue
            suggestions.append(s)
            used_positions.add(s["position"])

        # If we didn't get 3 with diversity, fill from top of list
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
    """Generate a human-readable reason for the suggestion."""
    if need >= 3:
        return f"You need a starting {position}. This is a high priority pick."
    elif need >= 1:
        return f"Adds depth at {position}. Projected {projected:.1f} pts/week."
    elif picks_made < 6:
        return f"Best player available. Elite {position} talent."
    else:
        return f"Strong value pick at {position}. Projected {projected:.1f} pts/week."


# ---------------------------------------------------------------------------
# Refresh draft from ESPN (call during live draft)
# ---------------------------------------------------------------------------

@router.post("/refresh")
async def refresh_draft_data():
    """Re-sync draft data from ESPN. Call this during a live draft to update the board."""
    import logging
    logger = logging.getLogger(__name__)

    try:
        from ..adapters.espn_adapter import get_league, get_draft_results, get_free_agents
        league = get_league()
        draft_picks = get_draft_results(league)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to ESPN: {str(e)}")

    db = await get_db()
    try:
        league_row = await db.execute_fetchall("SELECT id FROM league LIMIT 1")
        if not league_row:
            raise HTTPException(status_code=404, detail="League not synced")
        league_id = league_row[0]["id"]

        new_picks = 0
        for pick in draft_picks:
            espn_player_id = pick.get("espn_player_id")
            espn_team_id = pick.get("team_id")  # Note: key is "team_id" in adapter output

            if not espn_player_id or not espn_team_id:
                continue

            # Ensure player exists in DB
            cursor = await db.execute(
                "SELECT id FROM player WHERE espn_id = ?", (espn_player_id,)
            )
            p_row = await cursor.fetchone()
            if not p_row:
                # Insert the player from draft data
                await db.execute("""
                    INSERT OR IGNORE INTO player (espn_id, full_name, position, nfl_team)
                    VALUES (?, ?, ?, ?)
                """, (
                    espn_player_id,
                    pick.get("player_name", "Unknown"),
                    "??",  # Position might not be in draft data
                    None,
                ))
                cursor = await db.execute(
                    "SELECT id FROM player WHERE espn_id = ?", (espn_player_id,)
                )
                p_row = await cursor.fetchone()

            if not p_row:
                continue

            # Get team DB id
            cursor = await db.execute(
                "SELECT id FROM team WHERE espn_team_id = ? AND league_id = ?",
                (espn_team_id, league_id)
            )
            t_row = await cursor.fetchone()
            if not t_row:
                continue

            # Insert draft pick
            result = await db.execute("""
                INSERT OR IGNORE INTO draft_pick
                (league_id, team_id, player_id, round, pick_number, overall_pick)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                league_id, t_row["id"], p_row["id"],
                pick["round"], pick["pick_number"], pick["overall_pick"]
            ))
            if result.rowcount and result.rowcount > 0:
                new_picks += 1

        await db.commit()

        # Also try to fetch free agents to populate available players
        try:
            free_agents = get_free_agents(league, limit=200)
            for fa in free_agents:
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
                    fa.get("injury_status"), fa.get("projected_points", 0),
                ))
            await db.commit()
            fa_count = len(free_agents)
        except Exception as e:
            logger.warning("Could not fetch free agents: %s", e)
            fa_count = 0

        # Also sync rosters to update player positions for drafted players
        try:
            from ..adapters.espn_adapter import get_rosters
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
                            injury_status=excluded.injury_status,
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
            logger.warning("Could not sync rosters during draft refresh: %s", e)

        total_picks = await db.execute_fetchall(
            "SELECT COUNT(*) as cnt FROM draft_pick WHERE league_id = ?",
            (league_id,)
        )

        return {
            "status": "ok",
            "new_picks": new_picks,
            "total_picks": total_picks[0]["cnt"] if total_picks else 0,
            "free_agents_loaded": fa_count,
        }
    finally:
        await db.close()
