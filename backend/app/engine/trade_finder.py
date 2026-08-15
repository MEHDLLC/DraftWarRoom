"""
Trade finder: scans league rosters for mutually beneficial trade opportunities.
"""
from ..database import get_db


async def find_trade_suggestions(team_id: int, limit: int = 10) -> list[dict]:
    """
    Find potential trades that benefit both sides.
    Looks for position surplus/needs mismatches across league.
    """
    db = await get_db()
    try:
        # Get user's roster
        user_roster = await db.execute_fetchall("""
            SELECT p.id, p.full_name, p.position, p.composite_score, p.trade_value,
                   p.ros_projection
            FROM roster_entry re
            JOIN player p ON p.id = re.player_id
            WHERE re.team_id = ?
        """, (team_id,))
        user_players = [dict(r) for r in user_roster]

        # Identify user's surplus and needs
        user_pos = {}
        for p in user_players:
            user_pos.setdefault(p["position"], []).append(p)

        ideal = {"QB": 2, "RB": 4, "WR": 4, "TE": 2, "K": 1, "DST": 1}
        user_surplus = {}
        user_needs = {}
        for pos, ideal_count in ideal.items():
            count = len(user_pos.get(pos, []))
            if count > ideal_count:
                user_surplus[pos] = count - ideal_count
            elif count < ideal_count:
                user_needs[pos] = ideal_count - count

        if not user_surplus:
            return []

        # Get other teams
        other_teams = await db.execute_fetchall("""
            SELECT t.id, t.team_name, t.owner_name, t.espn_team_id
            FROM team t WHERE t.id != ?
        """, (team_id,))

        suggestions = []
        for team in other_teams:
            team = dict(team)
            # Get their roster
            their_roster = await db.execute_fetchall("""
                SELECT p.id, p.full_name, p.position, p.composite_score, p.trade_value,
                       p.ros_projection
                FROM roster_entry re
                JOIN player p ON p.id = re.player_id
                WHERE re.team_id = ?
            """, (team["id"],))
            their_players = [dict(r) for r in their_roster]

            their_pos = {}
            for p in their_players:
                their_pos.setdefault(p["position"], []).append(p)

            # Find complementary needs
            for surplus_pos, surplus_count in user_surplus.items():
                for need_pos in user_needs:
                    # Check if they have surplus where we need and need where we have surplus
                    their_count = len(their_pos.get(need_pos, []))
                    their_need_count = len(their_pos.get(surplus_pos, []))
                    their_ideal = ideal.get(need_pos, 2)
                    their_surplus_ideal = ideal.get(surplus_pos, 2)

                    if their_count > their_ideal and their_need_count < their_surplus_ideal:
                        # They have surplus at our need and need at our surplus
                        # Pick the best trade pair
                        our_give = sorted(
                            user_pos[surplus_pos],
                            key=lambda x: x["composite_score"] or 0,
                        )
                        # Give our worst surplus player
                        give_player = our_give[0] if our_give else None

                        their_give = sorted(
                            their_pos[need_pos],
                            key=lambda x: x["composite_score"] or 0,
                        )
                        receive_player = their_give[0] if their_give else None

                        if give_player and receive_player:
                            give_val = give_player.get("trade_value") or give_player.get("composite_score") or 0
                            recv_val = receive_player.get("trade_value") or receive_player.get("composite_score") or 0
                            mutual_benefit = min(give_val, recv_val)

                            suggestions.append({
                                "target_team": {
                                    "id": team["id"],
                                    "espn_team_id": team["espn_team_id"],
                                    "team_name": team["team_name"],
                                    "owner_name": team["owner_name"],
                                },
                                "give_players": [give_player],
                                "receive_players": [receive_player],
                                "explanation": (
                                    f"Trade your {surplus_pos} depth ({give_player['full_name']}) "
                                    f"to {team['team_name']} for {need_pos} help "
                                    f"({receive_player['full_name']}). "
                                    f"Both teams fill a roster need."
                                ),
                                "mutual_benefit_score": mutual_benefit,
                            })

        suggestions.sort(key=lambda x: x["mutual_benefit_score"], reverse=True)
        return suggestions[:limit]
    finally:
        await db.close()
