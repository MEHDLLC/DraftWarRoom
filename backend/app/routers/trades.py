from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..database import get_db
from ..schemas.models import PlayerInfo, TradeEvaluation, TradeSuggestion, TeamInfo

router = APIRouter()


class TradeRequest(BaseModel):
    give_player_ids: list[int]
    receive_player_ids: list[int]


async def _fetch_players(db, player_ids: list[int]) -> list[PlayerInfo]:
    """Fetch PlayerInfo objects for a list of player IDs."""
    if not player_ids:
        return []
    placeholders = ",".join("?" for _ in player_ids)
    rows = await db.execute_fetchall(
        f"SELECT * FROM player WHERE id IN ({placeholders})",
        tuple(player_ids),
    )
    found_ids = {r["id"] for r in rows}
    missing = set(player_ids) - found_ids
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Players not found: {sorted(missing)}",
        )
    return [
        PlayerInfo(
            id=r["id"],
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
        )
        for r in rows
    ]


@router.post("/analyze", response_model=TradeEvaluation)
async def analyze_trade(request: TradeRequest):
    """Analyze a proposed trade based on trade values, ROS projections, and roster fit."""
    if not request.give_player_ids or not request.receive_player_ids:
        raise HTTPException(
            status_code=400,
            detail="Both give_player_ids and receive_player_ids must be non-empty",
        )

    db = await get_db()
    try:
        give_players = await _fetch_players(db, request.give_player_ids)
        receive_players = await _fetch_players(db, request.receive_player_ids)

        # Try engine module
        try:
            from ..engine.trade_analyzer import analyze_trade as engine_analyze
            result = await engine_analyze(db, give_players, receive_players)
            return result
        except ImportError:
            pass

        # Fallback: simple trade-value-based analysis
        give_value = sum(p.trade_value for p in give_players)
        receive_value = sum(p.trade_value for p in receive_players)

        give_ros = sum(p.ros_projection for p in give_players)
        receive_ros = sum(p.ros_projection for p in receive_players)

        # Determine verdict
        value_diff = receive_value - give_value
        if abs(value_diff) < 5:
            verdict = "fair"
        elif value_diff > 0:
            verdict = "accept"
        else:
            verdict = "reject"

        # Build explanation
        give_names = ", ".join(p.full_name for p in give_players)
        receive_names = ", ".join(p.full_name for p in receive_players)

        explanation_parts = [
            f"Trading away {give_names} (total value: {give_value:.1f}) "
            f"for {receive_names} (total value: {receive_value:.1f}).",
        ]
        if value_diff > 0:
            explanation_parts.append(
                f"You gain {value_diff:.1f} in trade value."
            )
        elif value_diff < 0:
            explanation_parts.append(
                f"You lose {abs(value_diff):.1f} in trade value."
            )
        else:
            explanation_parts.append("Trade values are even.")

        ros_diff = receive_ros - give_ros
        if abs(ros_diff) > 1:
            direction = "gain" if ros_diff > 0 else "lose"
            explanation_parts.append(
                f"ROS projection impact: you {direction} {abs(ros_diff):.1f} total projected points."
            )

        # Roster impact summary
        give_positions = ", ".join(f"{p.position}" for p in give_players)
        receive_positions = ", ".join(f"{p.position}" for p in receive_players)
        roster_impact = (
            f"Sending: {give_positions}. Receiving: {receive_positions}."
        )

        return TradeEvaluation(
            give_players=give_players,
            receive_players=receive_players,
            give_value=round(give_value, 1),
            receive_value=round(receive_value, 1),
            verdict=verdict,
            explanation=" ".join(explanation_parts),
            roster_impact=roster_impact,
        )
    finally:
        await db.close()


@router.get("/suggestions", response_model=list[TradeSuggestion])
async def get_trade_suggestions():
    """Get AI-suggested trades that could improve the user's roster."""
    db = await get_db()
    try:
        # Get user team
        team_rows = await db.execute_fetchall("SELECT id FROM team WHERE is_user_team = 1 LIMIT 1")
        if not team_rows:
            raise HTTPException(status_code=404, detail="User team not identified")
        team_id = team_rows[0]["id"]

        # Try engine module
        try:
            from ..engine.trade_finder import find_trade_suggestions
            suggestions = await find_trade_suggestions(db, team_id)
            return suggestions
        except ImportError:
            pass

        # Fallback: identify positional weaknesses and find trade partners
        league_rows = await db.execute_fetchall("SELECT id FROM league LIMIT 1")
        if not league_rows:
            raise HTTPException(status_code=404, detail="League not synced yet")
        league_id = league_rows[0]["id"]

        # Get user roster grouped by position
        user_roster = await db.execute_fetchall(
            """
            SELECT p.id, p.full_name, p.position, p.composite_score,
                   p.trade_value, p.ros_projection, re.slot
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ?
            """,
            (team_id,),
        )

        # Calculate average composite by position for user
        pos_scores: dict[str, list[float]] = {}
        for r in user_roster:
            pos = r["position"]
            pos_scores.setdefault(pos, []).append(r["composite_score"] or 0)

        pos_avg = {pos: sum(s) / len(s) for pos, s in pos_scores.items() if s}

        # Find weakest position
        weak_positions = sorted(pos_avg.items(), key=lambda x: x[1])
        strong_positions = sorted(pos_avg.items(), key=lambda x: x[1], reverse=True)

        suggestions = []

        # For each weak position, look for trade targets on other teams
        for weak_pos, weak_score in weak_positions[:2]:
            # Find players at this position on other teams with higher scores
            targets = await db.execute_fetchall(
                """
                SELECT p.id, p.full_name, p.position, p.composite_score,
                       p.trade_value, p.ros_projection,
                       re.team_id, t.team_name, t.espn_team_id,
                       t.owner_name, t.wins, t.losses, t.ties,
                       t.points_for, t.points_against, t.is_user_team,
                       t.power_rank_score, t.playoff_probability
                FROM roster_entry re
                JOIN player p ON p.id = re.player_id
                JOIN team t ON t.id = re.team_id
                WHERE re.team_id != ?
                  AND p.position = ?
                  AND p.composite_score > ?
                  AND re.slot = 'BE'
                ORDER BY p.composite_score DESC
                LIMIT 3
                """,
                (team_id, weak_pos, weak_score),
            )

            for target in targets:
                # Find a user bench player at a strong position to offer
                for strong_pos, _ in strong_positions[:2]:
                    bench_offers = [
                        r for r in user_roster
                        if r["position"] == strong_pos and r["slot"] == "BE"
                    ]
                    if not bench_offers:
                        continue

                    offer = bench_offers[0]
                    if abs((offer["trade_value"] or 0) - (target["trade_value"] or 0)) < 20:
                        give_player = await _fetch_players(db, [offer["id"]])
                        receive_player = await _fetch_players(db, [target["id"]])

                        target_team = TeamInfo(
                            id=target["team_id"],
                            espn_team_id=target["espn_team_id"],
                            team_name=target["team_name"],
                            owner_name=target["owner_name"],
                            wins=target["wins"],
                            losses=target["losses"],
                            ties=target["ties"],
                            points_for=target["points_for"],
                            points_against=target["points_against"],
                            is_user_team=bool(target["is_user_team"]),
                            power_rank_score=target["power_rank_score"],
                            playoff_probability=target["playoff_probability"],
                        )

                        trade_value_diff = abs(
                            (offer["trade_value"] or 0) - (target["trade_value"] or 0)
                        )
                        benefit = max(0, 100 - trade_value_diff) / 100

                        suggestions.append(
                            TradeSuggestion(
                                target_team=target_team,
                                give_players=give_player,
                                receive_players=receive_player,
                                explanation=(
                                    f"Your {weak_pos} position is weak. "
                                    f"Trade {offer['full_name']} ({strong_pos}, bench) "
                                    f"for {target['full_name']} ({weak_pos}) "
                                    f"from {target['team_name']}."
                                ),
                                mutual_benefit_score=round(benefit, 2),
                            )
                        )
                        break  # One suggestion per target

        return suggestions
    finally:
        await db.close()
