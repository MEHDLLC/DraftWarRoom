import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  useLiveDraftState,
  useDraftSuggestions,
  useDraftRefresh,
  useAvailablePlayers,
  useMarkPicked,
  useUndoLastPick,
  useSetDraftOrder,
  useRemovePick,
} from "@/hooks/useDraft";
import { fetchApi } from "@/api/client";
import DraftValueTracker from "@/components/draft/DraftValueTracker";
import LoadingSpinner from "@/components/shared/LoadingSpinner";
import type {
  DraftSuggestion,
  AvailablePlayer,
  DraftOrderTeam,
  DraftTeamRoster,
} from "@/api/client";

// ---------------------------------------------------------------------------
// Position colors
// ---------------------------------------------------------------------------
const posColors: Record<string, string> = {
  QB: "bg-pink-500/20 text-pink-300",
  RB: "bg-emerald-500/20 text-emerald-300",
  WR: "bg-sky-500/20 text-sky-300",
  TE: "bg-orange-500/20 text-orange-300",
  K: "bg-purple-500/20 text-purple-300",
  DST: "bg-yellow-500/20 text-yellow-300",
  "D/ST": "bg-yellow-500/20 text-yellow-300",
};

// ---------------------------------------------------------------------------
// Backend team shape (from /league/teams)
// ---------------------------------------------------------------------------
interface LeagueTeam {
  id: number;
  team_name: string;
  owner_name: string | null;
  is_user_team: boolean;
}

// ---------------------------------------------------------------------------
// Setup: Set Draft Order (all teams)
// ---------------------------------------------------------------------------
function DraftOrderSetup({
  onSet,
  isPending,
}: {
  onSet: (order: { team_id: number; position: number }[]) => void;
  isPending: boolean;
}) {
  const { data: teams, isLoading } = useQuery({
    queryKey: ["league", "teams-for-draft"],
    queryFn: () => fetchApi<LeagueTeam[]>("/league/teams"),
  });

  const [assignments, setAssignments] = useState<Record<number, number>>({});

  // Auto-populate sequential positions when teams load
  const teamsReady = teams && teams.length > 0;
  if (teamsReady && Object.keys(assignments).length === 0) {
    const initial: Record<number, number> = {};
    teams.forEach((t, i) => {
      initial[t.id] = i + 1;
    });
    // This is only called once when teams first load
    setAssignments(initial);
  }

  const numTeams = teams?.length || 12;

  const handleChange = (teamId: number, position: number) => {
    setAssignments((prev) => {
      const next = { ...prev };
      // Swap: find who currently has this position and give them the old one
      const oldPos = prev[teamId];
      const otherTeamId = Object.entries(prev).find(
        ([, p]) => p === position
      )?.[0];
      if (otherTeamId) {
        next[Number(otherTeamId)] = oldPos;
      }
      next[teamId] = position;
      return next;
    });
  };

  const handleSubmit = () => {
    const order = Object.entries(assignments).map(([teamId, position]) => ({
      team_id: Number(teamId),
      position,
    }));
    onSet(order);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="md" label="Loading teams..." />
      </div>
    );
  }

  if (!teams || teams.length === 0) {
    return (
      <div className="mx-auto max-w-md rounded-xl border border-surface-700 bg-surface-800 p-6 text-center">
        <p className="text-sm text-surface-400">
          No teams found. Sync your league first.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg rounded-xl border border-surface-700 bg-surface-800 p-6">
      <h2 className="text-lg font-bold text-surface-100 text-center">
        Set Draft Order
      </h2>
      <p className="mt-2 text-sm text-surface-400 text-center">
        Assign each team their round 1 pick position. Snake draft order will be
        calculated automatically.
      </p>

      <div className="mt-4 space-y-2">
        {teams.map((team) => (
          <div
            key={team.id}
            className={[
              "flex items-center gap-3 rounded-lg px-3 py-2",
              team.is_user_team
                ? "border border-accent-500/30 bg-accent-500/5"
                : "bg-surface-700/30",
            ].join(" ")}
          >
            <select
              value={assignments[team.id] || 1}
              onChange={(e) => handleChange(team.id, Number(e.target.value))}
              className="w-20 rounded border border-surface-600 bg-surface-700 px-2 py-1 text-sm font-bold text-surface-100 focus:border-accent-500 focus:outline-none"
            >
              {Array.from({ length: numTeams }, (_, i) => (
                <option key={i + 1} value={i + 1}>
                  #{i + 1}
                </option>
              ))}
            </select>
            <span
              className={[
                "flex-1 truncate text-sm font-medium",
                team.is_user_team ? "text-accent-300" : "text-surface-200",
              ].join(" ")}
            >
              {team.team_name}
            </span>
            <span className="text-xs text-surface-500">
              {team.owner_name || ""}
            </span>
            {team.is_user_team && (
              <span className="rounded bg-accent-500/20 px-1.5 py-0.5 text-[10px] font-bold text-accent-400">
                YOU
              </span>
            )}
          </div>
        ))}
      </div>

      <button
        onClick={handleSubmit}
        disabled={isPending}
        className="btn-primary mt-5 w-full py-2.5 text-sm font-semibold"
      >
        {isPending ? "Setting..." : "Start Draft"}
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Now Picking Banner
// ---------------------------------------------------------------------------
function NowPickingBanner({
  currentTeam,
  currentPick,
  currentRound,
}: {
  currentTeam: { team_name: string; owner_name: string; is_user_team: boolean };
  currentPick: number | null;
  currentRound: number | null;
}) {
  if (currentTeam.is_user_team) {
    return (
      <div className="rounded-xl border-2 border-accent-400 bg-accent-500/10 p-4 text-center animate-pulse">
        <p className="text-lg font-bold text-accent-300">YOUR PICK!</p>
        <p className="text-xs text-accent-400">
          Pick #{currentPick} &middot; Round {currentRound}
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-surface-600 bg-surface-800 p-3 text-center">
      <p className="text-xs text-surface-500">Now Picking</p>
      <p className="text-base font-bold text-surface-100">
        {currentTeam.team_name}
      </p>
      <p className="text-xs text-surface-500">
        Pick #{currentPick} &middot; Round {currentRound}
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// All Team Rosters Accordion
// ---------------------------------------------------------------------------
function AllTeamRosters({
  draftOrder,
  allRosters,
  onRemove,
}: {
  draftOrder: DraftOrderTeam[];
  allRosters: Record<number, DraftTeamRoster[]>;
  onRemove?: (overallPick: number, playerName: string) => void;
}) {
  const [expandedTeam, setExpandedTeam] = useState<number | null>(null);

  return (
    <div className="rounded-xl border border-surface-700 bg-surface-800">
      <div className="border-b border-surface-700 px-4 py-2.5">
        <h3 className="text-sm font-semibold text-surface-200">All Teams</h3>
      </div>
      <div className="divide-y divide-surface-700/50">
        {draftOrder.map((team) => {
          const roster = allRosters[team.team_id] || [];
          const isExpanded = expandedTeam === team.team_id;

          return (
            <div key={team.team_id}>
              <button
                onClick={() =>
                  setExpandedTeam(isExpanded ? null : team.team_id)
                }
                className={[
                  "flex w-full items-center gap-2 px-4 py-2 text-left transition-colors hover:bg-surface-700/30",
                  team.is_user_team ? "bg-accent-500/5" : "",
                ].join(" ")}
              >
                <span className="w-6 text-xs font-bold text-surface-500">
                  #{team.draft_position}
                </span>
                <span
                  className={[
                    "flex-1 truncate text-sm font-medium",
                    team.is_user_team
                      ? "text-accent-300"
                      : "text-surface-200",
                  ].join(" ")}
                >
                  {team.team_name}
                </span>
                <span className="text-xs text-surface-500">
                  {roster.length} picks
                </span>
                <span className="text-xs text-surface-600">
                  {isExpanded ? "\u25B2" : "\u25BC"}
                </span>
              </button>
              {isExpanded && roster.length > 0 && (
                <div className="border-t border-surface-700/30 bg-surface-900/30">
                  {roster.map((p) => {
                    const posClass =
                      posColors[p.position] ||
                      "bg-surface-700 text-surface-300";
                    return (
                      <div
                        key={p.overall_pick}
                        className="flex items-center gap-2 px-6 py-1.5"
                      >
                        <span className="w-5 text-[10px] text-surface-600">
                          R{p.round}
                        </span>
                        <span
                          className={`rounded px-1 py-0.5 text-[10px] font-bold ${posClass}`}
                        >
                          {p.position}
                        </span>
                        <span className="flex-1 truncate text-xs text-surface-300">
                          {p.full_name}
                        </span>
                        <span className="text-[10px] text-surface-600">
                          {p.nfl_team}
                        </span>
                        {onRemove && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              if (
                                window.confirm(
                                  `Remove ${p.full_name} (pick #${p.overall_pick})? Subsequent picks will shift down.`
                                )
                              ) {
                                onRemove(p.overall_pick, p.full_name);
                              }
                            }}
                            className="ml-1 rounded p-0.5 text-danger-400/70 hover:bg-danger-500/20 hover:text-danger-300 transition-colors"
                            title={`Remove pick #${p.overall_pick}`}
                          >
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              className="h-3.5 w-3.5"
                              viewBox="0 0 20 20"
                              fill="currentColor"
                            >
                              <path
                                fillRule="evenodd"
                                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                                clipRule="evenodd"
                              />
                            </svg>
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
              {isExpanded && roster.length === 0 && (
                <div className="px-6 py-2 text-xs text-surface-600">
                  No picks yet
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Suggestion Card
// ---------------------------------------------------------------------------
function SuggestionCard({
  suggestion,
  rank,
  onPick,
}: {
  suggestion: DraftSuggestion;
  rank: number;
  onPick: () => void;
}) {
  const posClass =
    posColors[suggestion.position] || "bg-surface-700 text-surface-300";

  return (
    <div className="flex items-center gap-3 rounded-xl border border-accent-500/30 bg-accent-500/5 p-3">
      <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-accent-500/20 text-base font-bold text-accent-400">
        {rank}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className={`rounded px-1.5 py-0.5 text-xs font-bold ${posClass}`}>
            {suggestion.position}
          </span>
          <span className="truncate font-semibold text-surface-100 text-sm">
            {suggestion.full_name}
          </span>
          {suggestion.nfl_team && (
            <span className="text-xs text-surface-500">
              {suggestion.nfl_team}
            </span>
          )}
        </div>
        <p className="mt-0.5 text-xs text-surface-400">{suggestion.reason}</p>
      </div>
      <div className="flex flex-col items-end gap-1">
        <span className="text-sm font-bold text-accent-400">
          {suggestion.projected_points} pts
        </span>
        <button
          onClick={onPick}
          className="rounded bg-accent-500/20 px-2 py-0.5 text-xs font-semibold text-accent-300 hover:bg-accent-500/40 transition-colors"
        >
          Draft
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Player Row (available player in search results)
// ---------------------------------------------------------------------------
function PlayerRow({
  player,
  onPick,
  isPicking,
}: {
  player: AvailablePlayer;
  onPick: () => void;
  isPicking: boolean;
}) {
  const posClass =
    posColors[player.position] || "bg-surface-700 text-surface-300";

  return (
    <div className="flex items-center gap-3 border-b border-surface-700/50 px-3 py-2 last:border-b-0 hover:bg-surface-700/20 transition-colors">
      <span className={`rounded px-1.5 py-0.5 text-xs font-bold ${posClass}`}>
        {player.position}
      </span>
      <span className="flex-1 truncate text-sm font-medium text-surface-200">
        {player.full_name}
      </span>
      <span className="text-xs text-surface-500">{player.nfl_team}</span>
      <span className="w-16 text-right text-xs text-surface-400">
        {player.projected_points} pts
      </span>
      <button
        onClick={onPick}
        disabled={isPicking}
        className="rounded-lg bg-surface-700 px-3 py-1 text-xs font-medium text-surface-300 hover:bg-danger-500/20 hover:text-danger-300 transition-colors disabled:opacity-50"
      >
        Picked
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Draft Page
// ---------------------------------------------------------------------------
export default function DraftPage() {
  const [tab, setTab] = useState<"live" | "value">("live");
  const [search, setSearch] = useState("");
  const [posFilter, setPosFilter] = useState("");

  const { data: liveState, isLoading: stateLoading } = useLiveDraftState();
  const { data: suggestions } = useDraftSuggestions(
    !!liveState && liveState.picks_made > 0
  );
  const { data: available, isLoading: availLoading } = useAvailablePlayers(
    search,
    posFilter
  );

  const refreshMutation = useDraftRefresh();
  const markPicked = useMarkPicked();
  const undoLast = useUndoLastPick();
  const setDraftOrder = useSetDraftOrder();
  const removePick = useRemovePick();

  const handlePick = (playerId: number) => {
    markPicked.mutate(playerId);
  };

  const needsSetup = liveState && !liveState.draft_order_set;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-50">Draft</h1>
          <p className="mt-0.5 text-sm text-surface-400">
            {liveState?.is_complete
              ? "Draft complete!"
              : liveState && liveState.picks_made > 0
                ? `Pick ${liveState.current_pick} of ${liveState.total} (Round ${liveState.current_round})`
                : "Live draft companion"}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => refreshMutation.mutate()}
            disabled={refreshMutation.isPending}
            className="btn-primary flex items-center gap-2 text-sm"
          >
            {refreshMutation.isPending ? <LoadingSpinner size="sm" /> : null}
            {refreshMutation.isPending ? "Loading..." : "Load Players"}
          </button>
          {liveState && liveState.picks_made > 0 && (
            <button
              onClick={() => undoLast.mutate()}
              disabled={undoLast.isPending}
              className="rounded-lg border border-surface-600 bg-surface-800 px-3 py-2 text-xs text-surface-400 hover:text-danger-300 hover:border-danger-500/30 transition-colors"
            >
              Undo
            </button>
          )}
        </div>
      </div>

      {/* Refresh result */}
      {refreshMutation.isSuccess && refreshMutation.data && (
        <div className="rounded-lg border border-success-500/30 bg-success-500/10 px-4 py-2 text-sm text-success-300">
          {refreshMutation.data.players_loaded} players loaded. Ready to draft!
        </div>
      )}

      {/* Undo result */}
      {undoLast.isSuccess && undoLast.data && (
        <div className="rounded-lg border border-warning-400/30 bg-warning-400/10 px-4 py-2 text-sm text-warning-300">
          Undid pick: {undoLast.data.undone}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl bg-surface-800 p-1">
        <button
          onClick={() => setTab("live")}
          className={[
            "flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-colors",
            tab === "live"
              ? "bg-surface-700 text-surface-100"
              : "text-surface-400 hover:text-surface-200",
          ].join(" ")}
        >
          Live Draft
        </button>
        <button
          onClick={() => setTab("value")}
          className={[
            "flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-colors",
            tab === "value"
              ? "bg-surface-700 text-surface-100"
              : "text-surface-400 hover:text-surface-200",
          ].join(" ")}
        >
          Value Tracker
        </button>
      </div>

      {tab === "live" ? (
        stateLoading ? (
          <div className="flex items-center justify-center py-20">
            <LoadingSpinner size="lg" label="Loading..." />
          </div>
        ) : needsSetup ? (
          <div className="space-y-6">
            <div className="rounded-lg border border-accent-500/30 bg-accent-500/5 px-4 py-3 text-sm text-accent-300">
              First, click "Load Players" above to pull in the full player pool
              from ESPN. Then set the draft order below.
            </div>
            <DraftOrderSetup
              onSet={(order) => setDraftOrder.mutate(order)}
              isPending={setDraftOrder.isPending}
            />
          </div>
        ) : (
          <div className="grid gap-4 lg:grid-cols-3">
            {/* Left column: Now Picking / Suggestions + Rosters */}
            <div className="space-y-4 lg:col-span-1">
              {/* Now Picking banner */}
              {liveState && liveState.current_team && !liveState.is_complete && (
                <NowPickingBanner
                  currentTeam={liveState.current_team}
                  currentPick={liveState.current_pick}
                  currentRound={liveState.current_round}
                />
              )}

              {/* Next pick info (when it's not user's turn) */}
              {liveState &&
                !liveState.is_user_turn &&
                liveState.user_next_pick && (
                  <div className="rounded-xl border border-surface-700 bg-surface-800 p-3 text-center">
                    <p className="text-xs text-surface-500">Your next pick</p>
                    <p className="text-lg font-bold text-surface-200">
                      #{liveState.user_next_pick}
                    </p>
                    <p className="text-xs text-surface-500">
                      {liveState.user_next_pick -
                        (liveState.current_pick || 0)}{" "}
                      picks away
                    </p>
                  </div>
                )}

              {/* Suggestions */}
              {suggestions && suggestions.suggestions.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-semibold text-surface-300">
                    {liveState?.is_user_turn
                      ? "Recommended Picks:"
                      : "Best Available For You:"}
                  </h3>
                  {suggestions.suggestions.map((s, i) => (
                    <SuggestionCard
                      key={s.id}
                      suggestion={s}
                      rank={i + 1}
                      onPick={() => handlePick(s.id)}
                    />
                  ))}
                </div>
              )}

              {/* Your Roster */}
              {liveState && liveState.user_roster.length > 0 && (
                <div className="rounded-xl border border-surface-700 bg-surface-800">
                  <div className="border-b border-surface-700 px-4 py-2.5">
                    <h3 className="text-sm font-semibold text-surface-200">
                      Your Roster ({liveState.user_roster.length})
                    </h3>
                  </div>
                  <div className="divide-y divide-surface-700/50">
                    {liveState.user_roster.map((p) => {
                      const posClass =
                        posColors[p.position] ||
                        "bg-surface-700 text-surface-300";
                      return (
                        <div
                          key={p.overall_pick}
                          className="flex items-center gap-2 px-4 py-2"
                        >
                          <span className="w-6 text-xs text-surface-600">
                            R{p.round}
                          </span>
                          <span
                            className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${posClass}`}
                          >
                            {p.position}
                          </span>
                          <span className="flex-1 truncate text-sm font-medium text-surface-200">
                            {p.full_name}
                          </span>
                          <span className="text-xs text-surface-500">
                            {p.nfl_team}
                          </span>
                          <button
                            onClick={() => {
                              if (
                                window.confirm(
                                  `Remove ${p.full_name} (pick #${p.overall_pick})? Subsequent picks will shift down.`
                                )
                              ) {
                                removePick.mutate(p.overall_pick);
                              }
                            }}
                            className="ml-1 rounded p-0.5 text-danger-400/70 hover:bg-danger-500/20 hover:text-danger-300 transition-colors"
                            title={`Remove pick #${p.overall_pick}`}
                          >
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              className="h-3.5 w-3.5"
                              viewBox="0 0 20 20"
                              fill="currentColor"
                            >
                              <path
                                fillRule="evenodd"
                                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                                clipRule="evenodd"
                              />
                            </svg>
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Recent Picks */}
              {liveState && liveState.recent_picks.length > 0 && (
                <div className="rounded-xl border border-surface-700 bg-surface-800">
                  <div className="border-b border-surface-700 px-4 py-2.5">
                    <h3 className="text-sm font-semibold text-surface-200">
                      Recent Picks
                    </h3>
                  </div>
                  <div className="divide-y divide-surface-700/50">
                    {liveState.recent_picks.map((p) => {
                      const posClass =
                        posColors[p.position] ||
                        "bg-surface-700 text-surface-300";
                      return (
                        <div
                          key={p.overall_pick}
                          className={[
                            "flex items-center gap-2 px-4 py-2",
                            p.is_user_pick ? "bg-accent-500/5" : "",
                          ].join(" ")}
                        >
                          <span className="w-6 text-xs font-bold text-surface-500">
                            #{p.overall_pick}
                          </span>
                          <span
                            className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${posClass}`}
                          >
                            {p.position}
                          </span>
                          <span
                            className={[
                              "flex-1 truncate text-sm font-medium",
                              p.is_user_pick
                                ? "text-accent-300"
                                : "text-surface-300",
                            ].join(" ")}
                          >
                            {p.full_name}
                          </span>
                          <span className="text-xs text-surface-600">
                            {p.team_name}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* All Team Rosters */}
              {liveState &&
                liveState.draft_order_set &&
                liveState.draft_order.length > 0 && (
                  <AllTeamRosters
                    draftOrder={liveState.draft_order}
                    allRosters={liveState.all_rosters}
                    onRemove={(overallPick) => removePick.mutate(overallPick)}
                  />
                )}
            </div>

            {/* Right column: Available Players */}
            <div className="lg:col-span-2">
              <div className="rounded-xl border border-surface-700 bg-surface-800">
                <div className="border-b border-surface-700 p-3">
                  <div className="flex items-center gap-3">
                    <h3 className="text-sm font-semibold text-surface-200 flex-shrink-0">
                      Available
                    </h3>
                    {/* Search */}
                    <input
                      type="text"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      placeholder="Search players..."
                      className="flex-1 rounded-lg border border-surface-600 bg-surface-700 px-3 py-1.5 text-sm text-surface-100 placeholder:text-surface-500 focus:border-accent-500 focus:outline-none"
                    />
                    {/* Position filter */}
                    <select
                      value={posFilter}
                      onChange={(e) => setPosFilter(e.target.value)}
                      className="rounded-lg border border-surface-600 bg-surface-700 px-2 py-1.5 text-sm text-surface-200 focus:border-accent-500 focus:outline-none"
                    >
                      <option value="">All</option>
                      <option value="QB">QB</option>
                      <option value="RB">RB</option>
                      <option value="WR">WR</option>
                      <option value="TE">TE</option>
                      <option value="K">K</option>
                      <option value="D/ST">DST</option>
                    </select>
                  </div>
                </div>

                {/* Player list */}
                <div className="max-h-[600px] overflow-y-auto">
                  {availLoading ? (
                    <div className="flex items-center justify-center py-12">
                      <LoadingSpinner size="md" />
                    </div>
                  ) : !available || available.length === 0 ? (
                    <div className="py-12 text-center">
                      <p className="text-sm text-surface-500">
                        {search
                          ? "No players found matching your search."
                          : "No players loaded yet. Click 'Load Players' to fetch from ESPN."}
                      </p>
                    </div>
                  ) : (
                    available.map((player) => (
                      <PlayerRow
                        key={player.id}
                        player={player}
                        onPick={() => handlePick(player.id)}
                        isPicking={markPicked.isPending}
                      />
                    ))
                  )}
                </div>

                {/* Status bar */}
                {available && available.length > 0 && (
                  <div className="border-t border-surface-700 px-3 py-2 text-xs text-surface-500">
                    Showing {available.length} players
                    {liveState && ` \u00b7 ${liveState.picks_made} picked`}
                  </div>
                )}
              </div>
            </div>
          </div>
        )
      ) : (
        <DraftValueTracker />
      )}
    </div>
  );
}
