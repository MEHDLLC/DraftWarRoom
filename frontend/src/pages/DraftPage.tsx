import { useState } from "react";
import { useDraftBoard, useDraftSuggestions, useDraftRefresh } from "@/hooks/useDraft";
import DraftValueTracker from "@/components/draft/DraftValueTracker";
import LoadingSpinner from "@/components/shared/LoadingSpinner";
import type { DraftBoardPick, DraftBoardTeam, DraftSuggestion } from "@/api/client";

// ---------------------------------------------------------------------------
// Position color map
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

const posTextColors: Record<string, string> = {
  QB: "text-pink-300",
  RB: "text-emerald-300",
  WR: "text-sky-300",
  TE: "text-orange-300",
  K: "text-purple-300",
  DST: "text-yellow-300",
  "D/ST": "text-yellow-300",
};

// ---------------------------------------------------------------------------
// Suggestion Card
// ---------------------------------------------------------------------------
function SuggestionCard({ suggestion, rank }: { suggestion: DraftSuggestion; rank: number }) {
  const posClass = posColors[suggestion.position] || "bg-surface-700 text-surface-300";

  return (
    <div className="flex items-center gap-4 rounded-xl border border-surface-700 bg-surface-800 p-4 transition-colors hover:border-accent-500/40">
      <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-accent-500/20 text-lg font-bold text-accent-400">
        {rank}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className={`rounded px-1.5 py-0.5 text-xs font-bold ${posClass}`}>
            {suggestion.position}
          </span>
          <span className="truncate font-semibold text-surface-100">
            {suggestion.full_name}
          </span>
          {suggestion.nfl_team && (
            <span className="text-xs text-surface-500">{suggestion.nfl_team}</span>
          )}
        </div>
        <p className="mt-1 text-xs text-surface-400">{suggestion.reason}</p>
      </div>
      <div className="flex-shrink-0 text-right">
        <p className="text-sm font-bold text-accent-400">
          {suggestion.projected_points} pts
        </p>
        <p className="text-[10px] text-surface-500">projected</p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Draft Board Grid
// ---------------------------------------------------------------------------
function DraftBoardGrid({
  teams,
  picks,
  numTeams,
  totalRounds,
  currentPick,
}: {
  teams: DraftBoardTeam[];
  picks: DraftBoardPick[];
  numTeams: number;
  totalRounds: number;
  currentPick: number | null;
}) {
  // Build a lookup: (round, draft_position) -> pick
  const pickMap = new Map<string, DraftBoardPick>();
  for (const pick of picks) {
    const roundNum = pick.round;
    // Find draft position from espn_team_id
    const team = teams.find((t) => t.espn_team_id === pick.espn_team_id);
    if (team && team.draft_position) {
      pickMap.set(`${roundNum}-${team.draft_position}`, pick);
    }
  }

  // Calculate which cell is the "current pick"
  let currentRound: number | null = null;
  let currentPos: number | null = null;
  if (currentPick) {
    currentRound = Math.ceil(currentPick / numTeams);
    const posInRound = ((currentPick - 1) % numTeams);
    // Snake: even rounds reversed
    currentPos = currentRound % 2 === 0 ? numTeams - posInRound : posInRound + 1;
  }

  const maxRoundsToShow = Math.min(totalRounds, Math.max(picks.length > 0 ? Math.ceil(picks.length / numTeams) + 2 : 3, 3));

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[700px] border-collapse text-xs">
        <thead>
          <tr className="border-b border-surface-700">
            <th className="sticky left-0 z-10 bg-surface-900 px-2 py-2 text-left text-surface-500 font-medium">
              Rd
            </th>
            {teams.map((team) => (
              <th
                key={team.id}
                className={[
                  "px-1 py-2 text-center font-medium whitespace-nowrap",
                  team.is_user_team
                    ? "text-accent-400 bg-accent-500/5"
                    : "text-surface-500",
                ].join(" ")}
                title={`${team.team_name} (${team.owner_name})`}
              >
                <div className="max-w-[80px] truncate">
                  {team.team_name.length > 10
                    ? team.team_name.split(" ").map(w => w[0]).join("").slice(0, 4)
                    : team.team_name}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: maxRoundsToShow }, (_, roundIdx) => {
            const round = roundIdx + 1;
            // Snake: even rounds reverse the column order
            const isReversed = round % 2 === 0;

            return (
              <tr key={round} className="border-b border-surface-700/50">
                <td className="sticky left-0 z-10 bg-surface-900 px-2 py-1 text-surface-500 font-medium">
                  {round}
                </td>
                {teams.map((team, colIdx) => {
                  const draftPos = isReversed
                    ? numTeams - colIdx
                    : colIdx + 1;
                  const pick = pickMap.get(`${round}-${draftPos}`);
                  const isCurrent =
                    currentRound === round && currentPos === draftPos;
                  const isUserCol = team.is_user_team;

                  return (
                    <td
                      key={team.id}
                      className={[
                        "px-1 py-1 text-center",
                        isCurrent
                          ? "bg-accent-500/20 ring-1 ring-inset ring-accent-500/50"
                          : isUserCol
                            ? "bg-accent-500/5"
                            : "",
                      ].join(" ")}
                    >
                      {pick ? (
                        <div
                          className="rounded px-1 py-0.5"
                          title={`${pick.player_name} (${pick.position}) - ${pick.nfl_team}`}
                        >
                          <span
                            className={[
                              "block truncate font-medium",
                              pick.is_user_team
                                ? "text-accent-300"
                                : "text-surface-200",
                            ].join(" ")}
                          >
                            {pick.player_name.split(" ").slice(-1)[0]}
                          </span>
                          <span
                            className={[
                              "text-[10px] font-bold",
                              posTextColors[pick.position] || "text-surface-400",
                            ].join(" ")}
                          >
                            {pick.position}
                          </span>
                        </div>
                      ) : isCurrent ? (
                        <div className="animate-pulse rounded bg-accent-500/30 px-1 py-1.5">
                          <span className="text-[10px] font-bold text-accent-300">
                            NOW
                          </span>
                        </div>
                      ) : (
                        <div className="py-1.5 text-surface-700">-</div>
                      )}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Position Counter (shows what positions you've drafted)
// ---------------------------------------------------------------------------
function PositionCounter({ counts }: { counts: Record<string, number> }) {
  const positions = ["QB", "RB", "WR", "TE", "K", "DST"];
  const targets: Record<string, number> = { QB: 1, RB: 5, WR: 5, TE: 1, K: 1, DST: 1 };

  return (
    <div className="flex flex-wrap gap-2">
      {positions.map((pos) => {
        const have = counts[pos] || counts[pos === "DST" ? "D/ST" : ""] || 0;
        const target = targets[pos] || 1;
        const posClass = posColors[pos] || "bg-surface-700 text-surface-300";
        const met = have >= target;

        return (
          <div
            key={pos}
            className={[
              "flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium",
              met ? "opacity-50" : "",
              posClass,
            ].join(" ")}
          >
            <span className="font-bold">{pos}</span>
            <span className="text-[10px]">
              {have}/{target}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Draft Page
// ---------------------------------------------------------------------------
export default function DraftPage() {
  const [tab, setTab] = useState<"board" | "value">("board");
  const [autoRefresh, setAutoRefresh] = useState(false);

  const {
    data: board,
    isLoading: boardLoading,
    isError: boardError,
  } = useDraftBoard(autoRefresh);

  const { data: suggestions } = useDraftSuggestions(
    !!board && board.picks_made > 0
  );

  const refreshMutation = useDraftRefresh();

  const handleRefresh = () => {
    refreshMutation.mutate();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-50">Draft</h1>
          <p className="mt-1 text-surface-400">
            {board?.is_active
              ? "Draft in progress - tracking picks live"
              : board?.is_complete
                ? "Draft complete - review your picks"
                : "Draft board and pick suggestions"}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Auto-refresh toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={[
              "flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium transition-colors",
              autoRefresh
                ? "bg-success-500/20 text-success-400 ring-1 ring-success-500/30"
                : "bg-surface-800 text-surface-400 hover:text-surface-200",
            ].join(" ")}
          >
            <span
              className={[
                "h-2 w-2 rounded-full",
                autoRefresh ? "bg-success-400 animate-pulse" : "bg-surface-600",
              ].join(" ")}
            />
            {autoRefresh ? "Live" : "Auto-refresh off"}
          </button>

          {/* Manual refresh */}
          <button
            onClick={handleRefresh}
            disabled={refreshMutation.isPending}
            className="btn-primary flex items-center gap-2 text-sm"
          >
            {refreshMutation.isPending ? (
              <LoadingSpinner size="sm" />
            ) : (
              <svg
                className="h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <polyline points="23 4 23 10 17 10" />
                <polyline points="1 20 1 14 7 14" />
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10" />
                <path d="M20.49 15a9 9 0 0 1-14.85 3.36L1 14" />
              </svg>
            )}
            Refresh from ESPN
          </button>
        </div>
      </div>

      {/* Refresh result */}
      {refreshMutation.isSuccess && refreshMutation.data && (
        <div className="rounded-lg border border-success-500/30 bg-success-500/10 px-4 py-2.5 text-sm text-success-300">
          Synced {refreshMutation.data.total_picks} picks ({refreshMutation.data.new_picks} new),{" "}
          {refreshMutation.data.free_agents_loaded} available players loaded.
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl bg-surface-800 p-1">
        <button
          onClick={() => setTab("board")}
          className={[
            "flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-colors",
            tab === "board"
              ? "bg-surface-700 text-surface-100"
              : "text-surface-400 hover:text-surface-200",
          ].join(" ")}
        >
          Live Board
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

      {tab === "board" ? (
        <>
          {/* Suggestions panel */}
          {board && board.picks_made > 0 && suggestions && suggestions.suggestions.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-surface-100">
                    {board.is_user_turn ? (
                      <span className="text-accent-400">Your Pick! Choose wisely:</span>
                    ) : (
                      "Suggested Next Picks"
                    )}
                  </h2>
                  <p className="text-xs text-surface-500">
                    Based on your team needs &middot; Pick {board.picks_made + 1} of{" "}
                    {board.expected_total}
                    {board.user_next_pick && !board.is_user_turn && (
                      <span> &middot; Your next pick: #{board.user_next_pick}</span>
                    )}
                  </p>
                </div>
                {suggestions.position_counts && (
                  <PositionCounter counts={suggestions.position_counts} />
                )}
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                {suggestions.suggestions.map((s, idx) => (
                  <SuggestionCard key={s.id} suggestion={s} rank={idx + 1} />
                ))}
              </div>
            </div>
          )}

          {/* Draft Board */}
          {boardLoading ? (
            <div className="flex items-center justify-center py-20">
              <LoadingSpinner size="lg" label="Loading draft board..." />
            </div>
          ) : boardError ? (
            <div className="rounded-xl border border-danger-400/30 bg-danger-400/5 p-6 text-center">
              <p className="text-sm text-danger-300">
                Failed to load draft board. Try refreshing.
              </p>
            </div>
          ) : board && board.picks_made === 0 ? (
            <div className="rounded-xl border border-surface-700 bg-surface-800 p-8 text-center">
              <div className="mx-auto h-16 w-16 rounded-full bg-surface-700 flex items-center justify-center">
                <svg className="h-8 w-8 text-surface-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="2" y="3" width="20" height="14" rx="2" />
                  <path d="M8 21h8" />
                  <path d="M12 17v4" />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-semibold text-surface-200">
                Draft hasn't started yet
              </h3>
              <p className="mt-2 text-sm text-surface-400 max-w-md mx-auto">
                When the draft begins, click "Refresh from ESPN" to start tracking picks.
                Turn on auto-refresh to update every 15 seconds automatically.
              </p>
              <div className="mt-6 rounded-lg bg-surface-700/50 p-4 text-left max-w-sm mx-auto">
                <h4 className="text-sm font-semibold text-accent-400">Quick Draft Tips:</h4>
                <ul className="mt-2 space-y-1 text-xs text-surface-300">
                  <li>1. Take RBs and WRs in the first 4-5 rounds</li>
                  <li>2. Wait on QB until rounds 6-8</li>
                  <li>3. Don't draft K or DST until the last 2 rounds</li>
                  <li>4. Handcuff your top RB in later rounds</li>
                </ul>
              </div>
            </div>
          ) : board ? (
            <div className="space-y-4">
              {/* Status bar */}
              <div className="flex flex-wrap items-center gap-4 rounded-xl border border-surface-700 bg-surface-800 px-4 py-3">
                <div className="flex items-center gap-2">
                  <span
                    className={[
                      "h-2.5 w-2.5 rounded-full",
                      board.is_active
                        ? "bg-success-400 animate-pulse"
                        : board.is_complete
                          ? "bg-surface-500"
                          : "bg-warning-400",
                    ].join(" ")}
                  />
                  <span className="text-sm font-medium text-surface-200">
                    {board.is_active
                      ? "Draft In Progress"
                      : board.is_complete
                        ? "Draft Complete"
                        : "Pre-Draft"}
                  </span>
                </div>
                <span className="text-xs text-surface-500">
                  {board.picks_made} / {board.expected_total} picks
                </span>
                {board.is_active && (
                  <div className="ml-auto flex items-center gap-2">
                    <span className="text-xs text-surface-400">
                      Round {Math.ceil((board.current_pick || 1) / board.num_teams)}
                    </span>
                    <span className="text-xs text-surface-500">&middot;</span>
                    <span className="text-xs text-surface-400">
                      Pick #{board.current_pick}
                    </span>
                  </div>
                )}
              </div>

              {/* Board grid */}
              <div className="rounded-xl border border-surface-700 bg-surface-800/50 overflow-hidden">
                <DraftBoardGrid
                  teams={board.teams}
                  picks={board.picks}
                  numTeams={board.num_teams}
                  totalRounds={board.total_rounds}
                  currentPick={board.current_pick}
                />
              </div>

              {/* Recent picks feed */}
              {board.picks.length > 0 && (
                <div className="rounded-xl border border-surface-700 bg-surface-800 p-4">
                  <h3 className="text-sm font-semibold text-surface-200 mb-3">
                    Recent Picks
                  </h3>
                  <div className="space-y-2">
                    {board.picks
                      .slice(-8)
                      .reverse()
                      .map((pick) => {
                        const posClass =
                          posColors[pick.position] ||
                          "bg-surface-700 text-surface-300";
                        return (
                          <div
                            key={pick.overall_pick}
                            className={[
                              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm",
                              pick.is_user_team
                                ? "bg-accent-500/10 border border-accent-500/20"
                                : "bg-surface-700/30",
                            ].join(" ")}
                          >
                            <span className="w-8 text-xs font-bold text-surface-500">
                              #{pick.overall_pick}
                            </span>
                            <span
                              className={`rounded px-1.5 py-0.5 text-xs font-bold ${posClass}`}
                            >
                              {pick.position}
                            </span>
                            <span
                              className={[
                                "flex-1 font-medium",
                                pick.is_user_team
                                  ? "text-accent-300"
                                  : "text-surface-200",
                              ].join(" ")}
                            >
                              {pick.player_name}
                            </span>
                            <span className="text-xs text-surface-500">
                              {pick.team_name}
                            </span>
                          </div>
                        );
                      })}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </>
      ) : (
        <DraftValueTracker />
      )}
    </div>
  );
}
