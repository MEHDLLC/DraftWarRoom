import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useLeague } from "@/context/LeagueContext";
import { useLineupAdvice } from "@/hooks/useLineup";
import { lineupApi } from "@/api/client";
import type { ApplyLineupResult, LineupRecommendation } from "@/api/client";
import PlayerSlotCard from "@/components/lineup/PlayerSlotCard";
import type { PlayerSlotData } from "@/components/lineup/PlayerSlotCard";
import SwapSuggestion from "@/components/lineup/SwapSuggestion";
import LoadingSpinner from "@/components/shared/LoadingSpinner";
import EmptyState from "@/components/shared/EmptyState";

/** Map backend injury/bye state to the short status labels the card renders. */
function toStatusLabel(player: LineupRecommendation): string | undefined {
  if (player.on_bye) return "BYE";
  const status = player.injury_status?.toUpperCase();
  if (!status || status === "ACTIVE" || status === "NORMAL") return undefined;
  if (status === "INJURED_RESERVE" || status === "INJURY_RESERVE") return "IR";
  if (status === "SUSPENSION") return "Suspended";
  return status.charAt(0) + status.slice(1).toLowerCase();
}

function toSlotData(player: LineupRecommendation): PlayerSlotData {
  return {
    id: String(player.player_id),
    name: player.player_name,
    position: player.position,
    team: player.nfl_team ?? "",
    slot: player.recommended_slot,
    projectedPoints: player.projected_points ?? 0,
    compositeScore: Math.round(player.composite_score ?? 0),
    matchupGrade: player.matchup_grade ?? undefined,
    boomProbability: player.boom_probability,
    bustProbability: player.bust_probability,
    status: toStatusLabel(player),
  };
}

export default function LineupPage() {
  const { isLoading: leagueLoading } = useLeague();
  const queryClient = useQueryClient();

  const {
    data: advice,
    isLoading: adviceLoading,
    isError: adviceError,
  } = useLineupAdvice();

  const isLoading = leagueLoading || adviceLoading;

  // Apply-to-ESPN flow: preview -> confirm -> result
  const [preview, setPreview] = useState<ApplyLineupResult | null>(null);
  const [applyResult, setApplyResult] = useState<ApplyLineupResult | null>(null);
  const [applyBusy, setApplyBusy] = useState(false);

  async function handlePreview() {
    setApplyBusy(true);
    setApplyResult(null);
    try {
      setPreview(await lineupApi.applyLineup(false));
    } catch {
      setApplyResult({
        moves: [], sent: false, dry_run: false, write_enabled: false,
        message: "Could not build a preview. Is your team identified and the league synced?",
      });
    } finally {
      setApplyBusy(false);
    }
  }

  async function handleConfirm() {
    setApplyBusy(true);
    try {
      const result = await lineupApi.applyLineup(true);
      setApplyResult(result);
      setPreview(null);
      if (result.sent) {
        // Roster changed on ESPN; refetch advice after the resync
        setTimeout(() => queryClient.invalidateQueries({ queryKey: ["lineup"] }), 5000);
      }
    } catch {
      setApplyResult({
        moves: [], sent: false, dry_run: false, write_enabled: false,
        message: "The apply request failed. Check the server logs.",
      });
      setPreview(null);
    } finally {
      setApplyBusy(false);
    }
  }

  const starters = advice?.starters ?? [];
  const bench = advice?.bench ?? [];
  const allPlayers = [...starters, ...bench];

  const projectedTotal = starters.reduce(
    (sum, p) => sum + (p.projected_points ?? 0),
    0,
  );

  // Resolve swap suggestions against the full roster for projections
  const swapSuggestions =
    advice?.swap_suggestions
      ?.map((swap) => {
        const benchPlayer = allPlayers.find(
          (p) => p.player_name === swap.bench_player,
        );
        const starter = allPlayers.find(
          (p) => p.player_name === swap.starter_player,
        );
        if (!benchPlayer || !starter) return null;
        return {
          benchPlayer: {
            name: benchPlayer.player_name,
            position: benchPlayer.position,
            projectedPoints: benchPlayer.projected_points ?? 0,
          },
          starter: {
            name: starter.player_name,
            position: starter.position,
            projectedPoints: starter.projected_points ?? 0,
          },
          reason: swap.reason,
        };
      })
      ?.filter(Boolean) ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-50">Lineup</h1>
          <p className="mt-1 text-surface-400">
            Recommended starters for this week, with injuries and byes
            filtered out
          </p>
        </div>
        {advice && (
          <div className="flex items-center gap-2">
            <span className="rounded-lg border border-surface-700 bg-surface-800 px-3 py-1.5 text-sm font-medium text-surface-100">
              Week {advice.week}
            </span>
            <button
              onClick={handlePreview}
              disabled={applyBusy}
              className="rounded-lg bg-primary-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-primary-500 disabled:opacity-50"
            >
              {applyBusy ? "Working..." : "Apply to ESPN"}
            </button>
          </div>
        )}
      </div>

      {/* Apply result banner */}
      {applyResult && (
        <div
          className={`card border ${
            applyResult.sent
              ? "border-success-400/40 bg-success-400/10"
              : "border-accent-400/40 bg-accent-400/10"
          }`}
        >
          <p className="text-sm text-surface-100">{applyResult.message}</p>
        </div>
      )}

      {/* Apply confirmation dialog */}
      {preview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="card w-full max-w-md space-y-4">
            <h2 className="text-lg font-semibold text-surface-50">
              Apply recommended lineup?
            </h2>
            {preview.moves.length === 0 ? (
              <p className="text-sm text-surface-300">{preview.message}</p>
            ) : (
              <>
                <ul className="space-y-1 text-sm text-surface-200">
                  {preview.moves.map((m, i) => (
                    <li key={i} className="flex justify-between">
                      <span>
                        {m.player_name}{" "}
                        <span className="text-surface-500">({m.position})</span>
                      </span>
                      <span className="tabular-nums">
                        {m.from_slot} → {m.to_slot}
                      </span>
                    </li>
                  ))}
                </ul>
                {!preview.write_enabled && (
                  <p className="text-xs text-accent-400">
                    Writes are currently disabled (dry-run mode): confirming
                    logs the exact ESPN request for validation without sending
                    it. Set ESPN_WRITE_ENABLED=true to go live.
                  </p>
                )}
              </>
            )}
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setPreview(null)}
                className="rounded-lg border border-surface-600 px-3 py-1.5 text-sm text-surface-300 hover:bg-surface-800"
              >
                Cancel
              </button>
              {preview.moves.length > 0 && (
                <button
                  onClick={handleConfirm}
                  disabled={applyBusy}
                  className="rounded-lg bg-primary-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-primary-500 disabled:opacity-50"
                >
                  {applyBusy
                    ? "Working..."
                    : preview.write_enabled
                      ? "Apply to ESPN"
                      : "Run dry run"}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex h-64 items-center justify-center">
          <LoadingSpinner size="lg" label="Analyzing your lineup..." />
        </div>
      )}

      {/* Error State */}
      {!isLoading && adviceError && (
        <div className="card flex flex-col items-center justify-center py-16 text-center">
          <svg
            className="mb-3 h-10 w-10 text-danger-400"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
          <p className="text-sm font-medium text-surface-300">
            Failed to load lineup data
          </p>
          <p className="mt-1 text-xs text-surface-500">
            Make sure your league is synced and your team is identified
          </p>
        </div>
      )}

      {/* Loaded Content */}
      {!isLoading && !adviceError && advice && (
        <>
          {/* Projected Total */}
          <div className="card flex items-center justify-between">
            <div>
              <p className="text-xs font-medium uppercase text-surface-500">
                Projected Total
              </p>
              <p className="text-3xl font-bold tabular-nums text-accent-400">
                {projectedTotal.toFixed(1)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-surface-500">Week {advice.week}</p>
              <p className="text-sm text-surface-400">
                {starters.length} starters / {bench.length} bench
              </p>
            </div>
          </div>

          {/* Swap Suggestions */}
          {swapSuggestions.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-surface-400">
                Recommended Swaps
              </h2>
              {swapSuggestions.map((swap, idx) =>
                swap ? (
                  <SwapSuggestion
                    key={idx}
                    benchPlayer={swap.benchPlayer}
                    starter={swap.starter}
                    reason={swap.reason}
                  />
                ) : null,
              )}
            </div>
          )}

          {/* Starters Section */}
          <div className="space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-surface-400">
              Recommended Starters
            </h2>
            {starters.length === 0 ? (
              <EmptyState
                title="No starters"
                description="No starter data available for this week"
              />
            ) : (
              <div className="space-y-2">
                {starters.map((player) => (
                  <PlayerSlotCard
                    key={player.player_id}
                    player={toSlotData(player)}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Bench Section */}
          <div className="space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-surface-400">
              Bench
            </h2>
            {bench.length === 0 ? (
              <EmptyState
                title="No bench players"
                description="No bench data available for this week"
              />
            ) : (
              <div className="space-y-2">
                {bench.map((player) => (
                  <PlayerSlotCard
                    key={player.player_id}
                    player={toSlotData(player)}
                  />
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {/* Empty State - no data at all */}
      {!isLoading && !adviceError && !advice && (
        <EmptyState
          title="No lineup data"
          description="Sync your league to start getting lineup recommendations"
        />
      )}
    </div>
  );
}
