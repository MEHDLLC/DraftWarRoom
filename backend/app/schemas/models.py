from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# --- League ---
class LeagueInfo(BaseModel):
    id: int
    espn_id: int
    name: str
    season: int
    current_week: int
    num_teams: int
    scoring_type: str


class TeamInfo(BaseModel):
    id: int
    espn_team_id: int
    team_name: str
    owner_name: Optional[str] = None
    wins: int = 0
    losses: int = 0
    ties: int = 0
    points_for: float = 0
    points_against: float = 0
    is_user_team: bool = False
    power_rank_score: Optional[float] = None
    playoff_probability: Optional[float] = None


# --- Player ---
class PlayerInfo(BaseModel):
    id: int
    espn_id: Optional[int] = None
    full_name: str
    position: str
    nfl_team: Optional[str] = None
    status: Optional[str] = None
    injury_status: Optional[str] = None
    projected_points: float = 0
    ros_projection: float = 0
    composite_score: float = 0
    trade_value: float = 0
    boom_probability: float = 0
    bust_probability: float = 0
    sleeper_trending_add: int = 0
    sleeper_trending_drop: int = 0
    headshot_url: Optional[str] = None


class PlayerWeeklyStat(BaseModel):
    week: int
    fantasy_points: float = 0
    projected_points: float = 0
    snap_count: int = 0
    snap_pct: float = 0
    targets: int = 0
    target_share: float = 0
    carries: int = 0
    red_zone_targets: int = 0
    red_zone_carries: int = 0


class RosterPlayer(BaseModel):
    player: PlayerInfo
    slot: str
    acquisition_type: Optional[str] = None


# --- Lineup ---
class LineupRecommendation(BaseModel):
    player_id: int
    player_name: str
    position: str
    recommended_slot: str
    composite_score: float
    explanation: str
    boom_probability: float = 0
    bust_probability: float = 0
    matchup_grade: Optional[str] = None


class LineupAdvice(BaseModel):
    week: int
    starters: list[LineupRecommendation]
    bench: list[LineupRecommendation]
    swap_suggestions: list[dict] = []


# --- Matchup ---
class MatchupInfo(BaseModel):
    week: int
    home_team: TeamInfo
    away_team: TeamInfo
    home_score: Optional[float] = None
    away_score: Optional[float] = None
    home_projected: Optional[float] = None
    away_projected: Optional[float] = None
    win_probability: Optional[float] = None


# --- Waiver ---
class WaiverRecommendation(BaseModel):
    player: PlayerInfo
    composite_score: float
    explanation: str
    suggested_drop: Optional[PlayerInfo] = None
    drop_explanation: Optional[str] = None


# --- Trade ---
class TradeEvaluation(BaseModel):
    give_players: list[PlayerInfo]
    receive_players: list[PlayerInfo]
    give_value: float
    receive_value: float
    verdict: str  # "accept", "reject", "fair"
    explanation: str
    roster_impact: str


class TradeSuggestion(BaseModel):
    target_team: TeamInfo
    give_players: list[PlayerInfo]
    receive_players: list[PlayerInfo]
    explanation: str
    mutual_benefit_score: float


# --- Schedule ---
class ScheduleEntry(BaseModel):
    week: int
    opponent: str
    is_home: bool
    matchup_grade: str  # A+, A, B+, B, C, D, F
    pa_rank: Optional[int] = None
    pa_ppg: Optional[float] = None


# --- Chat ---
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    role: str = "assistant"
    content: str


# --- Notifications ---
class NotificationInfo(BaseModel):
    id: int
    title: str
    body: str
    type: str
    priority: str = "normal"
    is_read: bool = False
    created_at: str


# --- Draft ---
class DraftPickInfo(BaseModel):
    round: int
    pick_number: int
    overall_pick: int
    player: PlayerInfo
    team: TeamInfo
    adp: Optional[float] = None
    value_diff: Optional[float] = None  # ADP - actual pick (positive = value)


# --- Dashboard ---
class DashboardStats(BaseModel):
    league: LeagueInfo
    user_team: TeamInfo
    record: str
    standing: int
    points_rank: int
    recent_trend: list[str]  # W, L, W, ...
    upcoming_matchup: Optional[MatchupInfo] = None
    alerts: list[NotificationInfo] = []


# --- Optimal Lineup ---
class OptimalLineupResult(BaseModel):
    week: int
    actual_points: float
    optimal_points: float
    points_left_on_bench: float
    optimal_roster: list[dict]


# --- Power Rankings ---
class PowerRanking(BaseModel):
    rank: int
    team: TeamInfo
    score: float
    trend: int = 0  # positive = moved up, negative = moved down
