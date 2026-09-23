"""Tests for the ESPN write adapter's move diffing and payload building."""
from backend.app.adapters.espn_write_adapter import (
    build_lineup_transaction,
    compute_lineup_moves,
)


ROSTER = [
    {"id": 1, "espn_id": 101, "full_name": "Joe Burrow", "position": "QB", "slot": "QB"},
    {"id": 2, "espn_id": 102, "full_name": "Brock Purdy", "position": "QB", "slot": "BE"},
    {"id": 3, "espn_id": 103, "full_name": "Chase Brown", "position": "RB", "slot": "RB"},
    {"id": 4, "espn_id": 104, "full_name": "Stash Guy", "position": "RB", "slot": "IR"},
    {"id": 5, "espn_id": None, "full_name": "No Espn Id", "position": "WR", "slot": "BE"},
]


def test_compute_lineup_moves_diffs_and_orders():
    recommended = {2: "QB", 3: "RB"}  # Purdy starts, Burrow implicitly benched
    moves = compute_lineup_moves(ROSTER, recommended)

    assert [(m["player_name"], m["from_slot"], m["to_slot"]) for m in moves] == [
        ("Joe Burrow", "QB", "BE"),   # bench moves come first
        ("Brock Purdy", "BE", "QB"),
    ]
    burrow, purdy = moves
    assert burrow["from_slot_id"] == 0 and burrow["to_slot_id"] == 20
    assert purdy["from_slot_id"] == 20 and purdy["to_slot_id"] == 0


def test_compute_lineup_moves_skips_ir_and_missing_espn_id():
    # Recommending an IR player or one without an espn_id produces no moves
    moves = compute_lineup_moves(ROSTER, {1: "QB", 3: "RB", 4: "RB", 5: "WR"})
    assert moves == []


def test_compute_lineup_moves_flex_and_dst_slots():
    roster = [
        {"id": 1, "espn_id": 201, "full_name": "Flex RB", "position": "RB", "slot": "BE"},
        {"id": 2, "espn_id": 202, "full_name": "Rams D/ST", "position": "DST", "slot": "BE"},
    ]
    moves = compute_lineup_moves(roster, {1: "FLEX", 2: "DST"})
    by_name = {m["player_name"]: m for m in moves}
    assert by_name["Flex RB"]["to_slot_id"] == 23
    assert by_name["Rams D/ST"]["to_slot_id"] == 16


def test_build_lineup_transaction_shape():
    moves = compute_lineup_moves(ROSTER, {2: "QB", 3: "RB"})
    payload = build_lineup_transaction(7, 3, moves)

    assert payload["type"] == "ROSTER"
    assert payload["teamId"] == 7
    assert payload["scoringPeriodId"] == 3
    assert payload["executionType"] == "EXECUTE"
    assert payload["isLeagueManager"] is False
    assert all(i["type"] == "LINEUP" for i in payload["items"])
    assert {i["playerId"] for i in payload["items"]} == {101, 102}
