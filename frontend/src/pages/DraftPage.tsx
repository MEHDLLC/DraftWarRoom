import { useState } from "react";
import {
  useLiveDraftState,
  useDraftSuggestions,
  useDraftRefresh,
  useAvailablePlayers,
  useMarkPicked,
  useUndoLastPick,
  useSetMyPosition,
} from "@/hooks/useDraft";
import DraftValueTracker from "@/components/draft/DraftValueTracker";
import LoadingSpinner from "@/components/shared/LoadingSpinner";
import type { DraftSuggestion, AvailablePlayer } from "@/api/client";

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
// Setup: Set Draft Position
// ---------------------------------------------------------------------------
function DraftPositionSetup({ numTeams, onSet }: { numTeams: number; onSet: (pos: number) => void }) {
  const [pos, setPos] = useState(1);

  return (
    <div className="mx-auto max-w-md rounded-xl border border-surface-700 bg-surface-800 p-6 text-center">
      <h2 className="text-lg font-bold text-surface-100">Set Your Draft Position</h2>
      <p className="mt-2 text-sm text-surface-400">
        What pick number are you in round 1?
      </p>
      <div className="mt-4 flex items-center justify-center gap-3">
        <select
          value={pos}
          onChange={(e) => setPos(Number(e.target.value))}
          className="rounded-lg border border-surface-600 bg-surface-700 px-4 py-2.5 text-lg font-bold text-surface-100 focus:border-accent-500 focus:outline-none"
        >
          {Array.from({ length: numTeams }, (_, i) => (
            <option key={i + 1} value={i + 1}>
              Pick #{i + 1}
            </option>
          ))}
        </select>
        <button onClick={() => onSet(pos)} className="btn-primary px-6 py-2.5 text-sm font-semibold">
          Set Position
        </button>
      </div>
      <p className="mt-3 text-xs text-surface-500">
        Snake draft: Round 1 you pick #{pos}, Round 2 you pick #{numTeams - pos + 1}, etc.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Suggestion Card
// ---------------------------------------------------------------------------
function SuggestionCard({ suggestion, rank, onPick }: { suggestion: DraftSuggestion; rank: number; onPick: () => void }) {
  const posClass = posColors[suggestion.position] || "bg-surface-700 text-surface-300";

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
            <span className="text-xs text-surface-500">{suggestion.nfl_team}</span>
          )}
        </div>
        <p className="mt-0.5 text-xs text-surface-400">{suggestion.reason}</p>
      </div>
      <div className="flex flex-col items-end gap-1">
        <span className="text-sm font-bold text-accent-400">{suggestion.projected_points} pts</span>
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
function PlayerRow({ player, onPick, isPicking }: { player: AvailablePlayer; onPick: () => void; isPicking: boolean }) {
  const posClass = posColors[player.position] || "bg-surface-700 text-surface-300";

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
  const { data: suggestions } = useDraftSuggestions(!!liveState && liveState.picks_made > 0);
  const { data: available, isLoading: availLoading } = useAvailablePlayers(search, posFilter);

  const refreshMutation = useDraftRefresh();
  const markPicked = useMarkPicked();
  const undoLast = useUndoLastPick();
  const setPosition = useSetMyPosition();

  const handlePick = (playerId: number) => {
    markPicked.mutate(playerId);
  };

  const needsSetup = liveState && liveState.user_draft_position === null;
  const numTeams = 12; // From league

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
            tab === "live" ? "bg-surface-700 text-surface-100" : "text-surface-400 hover:text-surface-200",
          ].join(" ")}
        >
          Live Draft
        </button>
        <button
          onClick={() => setTab("value")}
          className={[
            "flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-colors",
            tab === "value" ? "bg-surface-700 text-surface-100" : "text-surface-400 hover:text-surface-200",
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
              First, click "Load Players" above to pull in the full player pool from ESPN.
            </div>
            <DraftPositionSetup
              numTeams={numTeams}
              onSet={(pos) => setPosition.mutate(pos)}
            />
          </div>
        ) : (
          <div className="grid gap-4 lg:grid-cols-3">
            {/* Left column: Your Turn / Suggestions + Your Roster */}
            <div className="space-y-4 lg:col-span-1">
              {/* Your Turn indicator */}
              {liveState && liveState.is_user_turn && (
                <div className="rounded-xl border-2 border-accent-400 bg-accent-500/10 p-4 text-center animate-pulse">
                  <p className="text-lg font-bold text-accent-300">YOUR PICK!</p>
                  <p className="text-xs text-accent-400">
                    Pick #{liveState.current_pick} &middot; Round {liveState.current_round}
                  </p>
                </div>
              )}

              {/* Next pick info */}
              {liveState && !liveState.is_user_turn && liveState.user_next_pick && (
                <div className="rounded-xl border border-surface-700 bg-surface-800 p-3 text-center">
                  <p className="text-xs text-surface-500">Your next pick</p>
                  <p className="text-lg font-bold text-surface-200">
                    #{liveState.user_next_pick}
                  </p>
                  <p className="text-xs text-surface-500">
                    {liveState.user_next_pick - (liveState.current_pick || 0)} picks away
                  </p>
                </div>
              )}

              {/* Suggestions */}
              {suggestions && suggestions.suggestions.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-semibold text-surface-300">
                    {liveState?.is_user_turn ? "Recommended Picks:" : "Best Available For You:"}
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
                      const posClass = posColors[p.position] || "bg-surface-700 text-surface-300";
                      return (
                        <div key={p.overall_pick} className="flex items-center gap-2 px-4 py-2">
                          <span className="w-6 text-xs text-surface-600">R{p.round}</span>
                          <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${posClass}`}>
                            {p.position}
                          </span>
                          <span className="flex-1 truncate text-sm font-medium text-surface-200">
                            {p.full_name}
                          </span>
                          <span className="text-xs text-surface-500">{p.nfl_team}</span>
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
                    <h3 className="text-sm font-semibold text-surface-200">Recent Picks</h3>
                  </div>
                  <div className="divide-y divide-surface-700/50">
                    {liveState.recent_picks.map((p) => {
                      const posClass = posColors[p.position] || "bg-surface-700 text-surface-300";
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
                          <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${posClass}`}>
                            {p.position}
                          </span>
                          <span className={[
                            "flex-1 truncate text-sm font-medium",
                            p.is_user_pick ? "text-accent-300" : "text-surface-300",
                          ].join(" ")}>
                            {p.full_name}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
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
                    {liveState && ` · ${liveState.picks_made} picked`}
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
