// ---------------------------------------------------------------------------
// DraftWarRoom API Client
// ---------------------------------------------------------------------------

const BASE_URL = "/api/v1";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ApiError {
  status: number;
  message: string;
  detail?: unknown;
}

export interface FetchOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined>;
}

export interface StreamCallbacks {
  onChunk: (chunk: string) => void;
  onDone?: () => void;
  onError?: (error: ApiError) => void;
}

// ---------------------------------------------------------------------------
// Base fetch wrapper
// ---------------------------------------------------------------------------

export async function fetchApi<T>(
  path: string,
  options: FetchOptions = {},
): Promise<T> {
  const { body, params, ...init } = options;

  let url = `${BASE_URL}${path}`;

  if (params) {
    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) {
        searchParams.set(key, String(value));
      }
    }
    const qs = searchParams.toString();
    if (qs) url += `?${qs}`;
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };

  const response = await fetch(url, {
    ...init,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let detail: unknown;
    try {
      detail = await response.json();
    } catch {
      // response body may not be JSON
    }
    const error: ApiError = {
      status: response.status,
      message: response.statusText || "Request failed",
      detail,
    };
    throw error;
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Streaming fetch helper (for chat)
// ---------------------------------------------------------------------------

export async function fetchStream(
  path: string,
  body: unknown,
  callbacks: StreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const url = `${BASE_URL}${path}`;

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    let detail: unknown;
    try {
      detail = await response.json();
    } catch {
      // non-JSON body
    }
    const error: ApiError = {
      status: response.status,
      message: response.statusText || "Stream request failed",
      detail,
    };
    callbacks.onError?.(error);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    callbacks.onError?.({ status: 0, message: "No readable stream" });
    return;
  }

  const decoder = new TextDecoder();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const text = decoder.decode(value, { stream: true });
      callbacks.onChunk(text);
    }
    callbacks.onDone?.();
  } catch (err) {
    if ((err as DOMException)?.name === "AbortError") return;
    callbacks.onError?.({
      status: 0,
      message: (err as Error).message ?? "Stream error",
    });
  }
}

// ---------------------------------------------------------------------------
// League API
// ---------------------------------------------------------------------------

export const leagueApi = {
  getInfo: () => fetchApi<LeagueInfo>("/league"),

  getTeams: () => fetchApi<Team[]>("/league/teams"),

  getRoster: (teamId?: string) =>
    fetchApi<Roster>("/league/roster", { params: { team_id: teamId } }),

  getDashboard: () => fetchApi<Dashboard>("/league/dashboard"),

  sync: () => fetchApi<SyncResult>("/league/sync", { method: "POST" }),

  getPowerRankings: () => fetchApi<PowerRanking[]>("/league/power-rankings"),
};

// ---------------------------------------------------------------------------
// Player API
// ---------------------------------------------------------------------------

export const playerApi = {
  getAll: (params?: { position?: string; search?: string; limit?: number }) =>
    fetchApi<Player[]>("/players", { params }),

  getById: (playerId: string) => fetchApi<PlayerDetail>(`/players/${playerId}`),

  getStats: (playerId: string, params?: { weeks?: number }) =>
    fetchApi<PlayerStats>(`/players/${playerId}/stats`, { params }),
};

// ---------------------------------------------------------------------------
// Lineup API
// ---------------------------------------------------------------------------

export const lineupApi = {
  getAdvice: (week?: number) =>
    fetchApi<LineupAdvice>("/lineup/advice", { params: { week } }),

  getOptimal: (week?: number) =>
    fetchApi<OptimalLineup>("/lineup/optimal", { params: { week } }),
};

// ---------------------------------------------------------------------------
// Matchup API
// ---------------------------------------------------------------------------

export const matchupApi = {
  getCurrent: () => fetchApi<Matchup>("/matchup/current"),

  getByWeek: (week: number) => fetchApi<Matchup>(`/matchup/week/${week}`),

  getAnalysis: (week?: number) =>
    fetchApi<MatchupAnalysis>("/matchup/analysis", { params: { week } }),
};

// ---------------------------------------------------------------------------
// Waiver API
// ---------------------------------------------------------------------------

export const waiverApi = {
  getRecommendations: (params?: { position?: string; limit?: number }) =>
    fetchApi<WaiverRecommendation[]>("/waivers/recommendations", { params }),

  getTrending: (params?: { period?: string }) =>
    fetchApi<TrendingPlayer[]>("/waivers/trending", { params }),
};

// ---------------------------------------------------------------------------
// Trade API
// ---------------------------------------------------------------------------

export const tradeApi = {
  analyze: (payload: TradeAnalysisRequest) =>
    fetchApi<TradeAnalysis>("/trades/analyze", {
      method: "POST",
      body: payload,
    }),

  getSuggestions: () => fetchApi<TradeSuggestion[]>("/trades/suggestions"),
};

// ---------------------------------------------------------------------------
// Schedule API
// ---------------------------------------------------------------------------

export const scheduleApi = {
  getSos: () => fetchApi<StrengthOfSchedule[]>("/schedule/sos"),

  getPlayoffs: () => fetchApi<PlayoffScenario>("/schedule/playoffs"),

  getByes: () => fetchApi<ByeWeek[]>("/schedule/byes"),
};

// ---------------------------------------------------------------------------
// Chat API
// ---------------------------------------------------------------------------

export const chatApi = {
  sendMessage: (message: string, callbacks: StreamCallbacks, signal?: AbortSignal) =>
    fetchStream("/chat/message", { message }, callbacks, signal),

  getHistory: () => fetchApi<ChatMessage[]>("/chat/history"),
};

// ---------------------------------------------------------------------------
// Notification API
// ---------------------------------------------------------------------------

export const notificationApi = {
  getAll: () => fetchApi<AppNotification[]>("/notifications"),

  markRead: (id: string) =>
    fetchApi<void>(`/notifications/${id}/read`, { method: "POST" }),

  getUnreadCount: () =>
    fetchApi<{ unread_count: number }>("/notifications/unread-count"),
};

// ---------------------------------------------------------------------------
// Draft API
// ---------------------------------------------------------------------------

export const draftApi = {
  getPicks: () => fetchApi<DraftPick[]>("/draft/picks"),

  getValueTracker: () => fetchApi<DraftValueTracker>("/draft/value-tracker"),

  getBoard: () => fetchApi<DraftBoard>("/draft/board"),

  getSuggestions: () => fetchApi<DraftSuggestions>("/draft/suggestions"),

  refresh: () => fetchApi<DraftRefreshResult>("/draft/refresh", { method: "POST" }),

  getLiveState: () => fetchApi<LiveDraftState>("/draft/live-state"),

  getAvailable: (params?: { q?: string; position?: string; limit?: number }) =>
    fetchApi<AvailablePlayer[]>("/draft/available", { params }),

  markPicked: (playerId: number) =>
    fetchApi<MarkPickedResult>("/draft/mark-picked", {
      method: "POST",
      body: { player_id: playerId },
    }),

  undoLast: () => fetchApi<{ status: string; undone: string }>("/draft/undo-last", { method: "DELETE" }),

  setMyPosition: (position: number) =>
    fetchApi<{ status: string; position: number }>("/draft/set-my-position", {
      method: "POST",
      body: { position },
    }),

  setDraftOrder: (order: { team_id: number; position: number }[]) =>
    fetchApi<{ status: string; num_teams: number }>("/draft/set-order", {
      method: "POST",
      body: { order },
    }),
};

// ---------------------------------------------------------------------------
// Shared API types
// ---------------------------------------------------------------------------

export interface LeagueInfo {
  id: string;
  name: string;
  platform: string;
  season: number;
  week: number;
  teamCount: number;
  scoringType: string;
  userTeamId: string;
}

export interface Team {
  id: string;
  name: string;
  owner: string;
  record: { wins: number; losses: number; ties: number };
  pointsFor: number;
  pointsAgainst: number;
  rank: number;
}

export interface Roster {
  teamId: string;
  players: RosterPlayer[];
}

export interface RosterPlayer {
  id: string;
  name: string;
  position: string;
  team: string;
  slot: string;
  projectedPoints: number;
  status?: string;
}

export interface Dashboard {
  teamSummary: Team;
  weekMatchup: Matchup;
  alerts: DashboardAlert[];
  quickStats: Record<string, number | string>;
}

export interface DashboardAlert {
  type: "info" | "warning" | "danger";
  title: string;
  message: string;
}

export interface SyncResult {
  success: boolean;
  lastSynced: string;
}

export interface PowerRanking {
  rank: number;
  teamId: string;
  teamName: string;
  score: number;
  trend: number;
}

export interface Player {
  id: string;
  name: string;
  position: string;
  team: string;
  status?: string;
  averagePoints: number;
  projectedPoints: number;
}

export interface PlayerDetail extends Player {
  seasonStats: Record<string, number>;
  weeklyPoints: number[];
  notes: string[];
}

export interface PlayerStats {
  playerId: string;
  weeklyStats: WeeklyStat[];
}

export interface WeeklyStat {
  week: number;
  points: number;
  stats: Record<string, number>;
}

export interface LineupAdvice {
  week: number;
  suggestions: LineupSuggestion[];
  reasoning: string;
}

export interface LineupSuggestion {
  action: "start" | "bench" | "flex";
  playerId: string;
  playerName: string;
  position: string;
  reason: string;
  confidence: number;
}

export interface OptimalLineup {
  week: number;
  starters: RosterPlayer[];
  bench: RosterPlayer[];
  projectedTotal: number;
}

export interface Matchup {
  week: number;
  homeTeam: MatchupTeam;
  awayTeam: MatchupTeam;
  winProbability: number;
}

export interface MatchupTeam {
  id: string;
  name: string;
  projectedScore: number;
  actualScore?: number;
}

export interface MatchupAnalysis {
  week: number;
  matchup: Matchup;
  keyPlayers: string[];
  analysis: string;
  winProbability: number;
}

export interface WaiverRecommendation {
  player: Player;
  priority: number;
  dropCandidate?: Player;
  reason: string;
  faabSuggestion?: number;
}

export interface TrendingPlayer {
  player: Player;
  addPercentage: number;
  dropPercentage: number;
  trend: "up" | "down";
}

export interface TradeAnalysisRequest {
  sendPlayerIds: string[];
  receivePlayerIds: string[];
  targetTeamId: string;
}

export interface TradeAnalysis {
  fairnessScore: number;
  winnerSide: "send" | "receive" | "even";
  impact: string;
  recommendation: string;
}

export interface TradeSuggestion {
  targetTeam: Team;
  sendPlayers: Player[];
  receivePlayers: Player[];
  rationale: string;
  fairnessScore: number;
}

export interface StrengthOfSchedule {
  teamId: string;
  teamName: string;
  remainingSos: number;
  rank: number;
  weeklyDifficulty: number[];
}

export interface PlayoffScenario {
  currentStanding: number;
  clinchScenario: string | null;
  eliminationScenario: string | null;
  playoffProbability: number;
}

export interface ByeWeek {
  week: number;
  teams: string[];
  rosterImpact: string[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface AppNotification {
  id: number;
  type: string;
  title: string;
  body: string;
  priority: string;
  is_read: boolean;
  created_at: string;
}

export interface DraftPick {
  round: number;
  pick: number;
  teamId: string;
  teamName: string;
  player?: Player;
}

export interface DraftValueTracker {
  picks: DraftPickValue[];
  bestAvailable: Player[];
  recommendations: string[];
}

export interface DraftPickValue {
  player: Player;
  adp: number;
  pickNumber: number;
  value: number; // positive = good value, negative = reach
}

export interface DraftBoardTeam {
  id: number;
  espn_team_id: number;
  team_name: string;
  owner_name: string;
  is_user_team: boolean;
  draft_position: number | null;
}

export interface DraftBoardPick {
  round: number;
  pick_number: number;
  overall_pick: number;
  player_name: string;
  position: string;
  nfl_team: string;
  projected_points: number;
  espn_team_id: number;
  team_name: string;
  is_user_team: boolean;
}

export interface DraftBoard {
  num_teams: number;
  total_rounds: number;
  picks_made: number;
  expected_total: number;
  is_active: boolean;
  is_complete: boolean;
  current_pick: number | null;
  current_team_espn_id: number | null;
  is_user_turn: boolean;
  user_next_pick: number | null;
  user_draft_position: number | null;
  teams: DraftBoardTeam[];
  picks: DraftBoardPick[];
}

export interface DraftSuggestion {
  id: number;
  full_name: string;
  position: string;
  nfl_team: string;
  projected_points: number;
  headshot_url: string | null;
  need_score: number;
  pick_score: number;
  reason: string;
}

export interface DraftSuggestions {
  suggestions: DraftSuggestion[];
  picks_made: number;
  total_roster: number;
  position_counts: Record<string, number>;
  message?: string;
}

export interface DraftRefreshResult {
  status: string;
  new_picks: number;
  players_loaded: number;
  free_agents_fetched: number;
}

export interface AvailablePlayer {
  id: number;
  full_name: string;
  position: string;
  nfl_team: string;
  projected_points: number;
  headshot_url: string | null;
}

export interface MarkPickedResult {
  status: string;
  overall_pick: number;
  round: number;
  pick_in_round: number;
  player_name: string;
  position: string;
  is_user_pick: boolean;
  team_name: string;
}

export interface LiveDraftRosterPlayer {
  full_name: string;
  position: string;
  nfl_team: string;
  projected_points: number;
  round: number;
  overall_pick: number;
}

export interface LiveDraftRecentPick {
  full_name: string;
  position: string;
  overall_pick: number;
  round: number;
  is_user_pick: boolean;
  team_name: string;
}

export interface DraftOrderTeam {
  team_id: number;
  team_name: string;
  owner_name: string;
  draft_position: number;
  is_user_team: boolean;
}

export interface DraftTeamRoster {
  full_name: string;
  position: string;
  nfl_team: string;
  projected_points: number;
  round: number;
  overall_pick: number;
}

export interface LiveDraftState {
  picks_made: number;
  total: number;
  current_pick: number | null;
  current_round: number | null;
  is_user_turn: boolean;
  user_next_pick: number | null;
  user_draft_position: number | null;
  is_complete: boolean;
  user_roster: LiveDraftRosterPlayer[];
  recent_picks: LiveDraftRecentPick[];
  draft_order: DraftOrderTeam[];
  draft_order_set: boolean;
  current_team: { team_id: number; team_name: string; owner_name: string; is_user_team: boolean } | null;
  all_rosters: Record<number, DraftTeamRoster[]>;
}
