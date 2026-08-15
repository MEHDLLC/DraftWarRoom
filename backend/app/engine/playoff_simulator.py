"""
Playoff probability simulator using Monte Carlo simulation.
Runs 10,000 simulations of remaining season to estimate playoff odds.
"""
import random
from ..database import get_db


async def simulate_playoffs(num_simulations: int = 10000) -> list[dict]:
    """
    Run Monte Carlo simulations of the remaining season.
    Returns playoff probability for each team.
    """
    db = await get_db()
    try:
        league_row = await db.execute_fetchall(
            "SELECT current_week, num_teams, playoff_start_week, id FROM league LIMIT 1"
        )
        if not league_row:
            return []

        current_week = league_row[0]["current_week"]
        num_teams = league_row[0]["num_teams"]
        playoff_start = league_row[0]["playoff_start_week"] or 15
        league_id = league_row[0]["id"]
        playoff_spots = max(num_teams // 2, 4)  # Typically half the league

        # Get current standings
        teams = await db.execute_fetchall(
            "SELECT id, team_name, wins, losses, ties, points_for FROM team WHERE league_id = ?",
            (league_id,)
        )
        teams = [dict(t) for t in teams]

        if not teams:
            return []

        # Get remaining matchups
        remaining_matchups = await db.execute_fetchall("""
            SELECT week, home_team_id, away_team_id, home_projected, away_projected
            FROM matchup
            WHERE league_id = ? AND week >= ? AND week < ? AND winner_team_id IS NULL
        """, (league_id, current_week, playoff_start))
        remaining = [dict(m) for m in remaining_matchups]

        # Calculate average points per team (for simulation variance)
        team_avgs = {}
        for team in teams:
            total_games = team["wins"] + team["losses"] + team["ties"]
            team_avgs[team["id"]] = team["points_for"] / max(total_games, 1)

        # Run simulations
        playoff_counts = {t["id"]: 0 for t in teams}

        for _ in range(num_simulations):
            # Copy current records
            sim_records = {
                t["id"]: {"wins": t["wins"], "losses": t["losses"],
                          "pf": t["points_for"]}
                for t in teams
            }

            # Simulate each remaining game
            for matchup in remaining:
                home_id = matchup["home_team_id"]
                away_id = matchup["away_team_id"]

                # Generate random scores based on team averages with variance
                home_avg = team_avgs.get(home_id, 100)
                away_avg = team_avgs.get(away_id, 100)
                std_dev = 20  # Typical weekly variance

                home_score = max(0, random.gauss(home_avg, std_dev))
                away_score = max(0, random.gauss(away_avg, std_dev))

                if home_score > away_score:
                    sim_records[home_id]["wins"] += 1
                    sim_records[away_id]["losses"] += 1
                else:
                    sim_records[away_id]["wins"] += 1
                    sim_records[home_id]["losses"] += 1

                sim_records[home_id]["pf"] += home_score
                sim_records[away_id]["pf"] += away_score

            # Determine playoff teams (by wins, then points for)
            standings = sorted(
                sim_records.items(),
                key=lambda x: (x[1]["wins"], x[1]["pf"]),
                reverse=True,
            )
            for team_id, _ in standings[:playoff_spots]:
                playoff_counts[team_id] += 1

        # Calculate probabilities and update DB
        results = []
        for team in teams:
            prob = (playoff_counts[team["id"]] / num_simulations) * 100
            results.append({
                "team_id": team["id"],
                "team_name": team["team_name"],
                "current_record": f"{team['wins']}-{team['losses']}",
                "playoff_probability": round(prob, 1),
            })

            # Update team record
            await db.execute(
                "UPDATE team SET playoff_probability = ? WHERE id = ?",
                (round(prob, 1), team["id"]),
            )

        await db.commit()
        results.sort(key=lambda x: x["playoff_probability"], reverse=True)
        return results
    finally:
        await db.close()
