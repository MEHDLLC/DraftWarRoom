"""Tests for the composite scoring engine."""
import pytest
from backend.app.engine.scorer import (
    percentile_rank,
    compute_composite_score,
    injury_to_score,
    usage_trend_score,
    generate_explanation,
)
from backend.app.engine.boom_bust import calculate_boom_bust, boom_bust_label


class TestPercentileRank:
    def test_basic_percentile(self):
        values = [10, 20, 30, 40, 50]
        assert percentile_rank(50, values) == 90.0
        assert percentile_rank(10, values) == 10.0

    def test_empty_list(self):
        assert percentile_rank(50, []) == 50.0

    def test_single_value(self):
        assert percentile_rank(50, [50]) == 50.0

    def test_middle_value(self):
        values = [10, 20, 30, 40, 50]
        result = percentile_rank(30, values)
        assert 30 < result < 70  # Should be near median


class TestCompositeScore:
    def test_high_scorer(self):
        score, breakdown = compute_composite_score(
            ros_projection=20.0, all_ros_projections=[5, 10, 15, 20, 25],
            usage_trend=80.0, all_usage_trends=[20, 40, 60, 80, 100],
            matchup_score=90.0, all_matchup_scores=[30, 50, 70, 90, 100],
            injury_score=100.0,
            community_score=500, all_community_scores=[0, 100, 200, 500, 1000],
        )
        assert score > 50  # Above average
        assert "ros_projection" in breakdown
        assert "usage_trend" in breakdown

    def test_low_scorer(self):
        score, _ = compute_composite_score(
            ros_projection=5.0, all_ros_projections=[5, 10, 15, 20, 25],
            usage_trend=20.0, all_usage_trends=[20, 40, 60, 80, 100],
            matchup_score=30.0, all_matchup_scores=[30, 50, 70, 90, 100],
            injury_score=0.0,
            community_score=0, all_community_scores=[0, 100, 200, 500, 1000],
        )
        assert score < 50


class TestInjuryScore:
    def test_healthy(self):
        assert injury_to_score("ACTIVE") == 100.0
        assert injury_to_score(None) == 100.0

    def test_questionable(self):
        assert injury_to_score("QUESTIONABLE") == 60.0

    def test_out(self):
        assert injury_to_score("OUT") == 0.0


class TestUsageTrend:
    def test_increasing_trend(self):
        # Last week weighted most: 80 * 3 + 60 * 2 + 40 * 1 = 400 / 6 = 66.67
        result = usage_trend_score([40, 60, 80])
        assert result > 55

    def test_empty(self):
        assert usage_trend_score([]) == 0.0


class TestBoomBust:
    def test_boom_heavy(self):
        # Player who often exceeds 1.5x average
        points = [10, 10, 25, 10, 30, 10, 28]  # avg ~17.5, boom threshold ~26
        boom, bust = calculate_boom_bust(points)
        assert boom > 0

    def test_steady_player(self):
        points = [12, 13, 11, 14, 12, 13, 11]
        boom, bust = calculate_boom_bust(points)
        assert boom == 0
        assert bust == 0

    def test_insufficient_data(self):
        boom, bust = calculate_boom_bust([10, 15])
        assert boom == 0.0
        assert bust == 0.0

    def test_label(self):
        assert boom_bust_label(35, 10) == "High Ceiling"
        assert boom_bust_label(5, 5) == "Steady Floor"
