import { useState } from "react";
import { useLeague } from "@/context/LeagueContext";
import { useLineupAdvice, useOptimalLineup } from "@/hooks/useLineup";
import PlayerSlotCard from "@/components/lineup/PlayerSlotCard";
import type { PlayerSlotData } from "@/components/lineup/PlayerSlotCard";
import SwapSuggestion from "@/components/lineup/SwapSuggestion";
import LoadingSpinner from "@/components/shared/LoadingSpinner";
import EmptyState from "@/components/shared/EmptyState";

export default function LineupPage() {
  const { league, isLoading: leagueLoading } = useLeague();
  const currentWeek = league?.week ?? 1;
  const [selectedWeek, setSelectedWeek] = useState<number | undefined>(
    undefined,
  );

  const week = selectedWeek ?? currentWeek;

  const {
    data: optimal,
    isLoading: optimalLoading,
    isError: optimalError,
  } = useOptimalLineup(week);

  const {
    data: advice,
    isLoading: adviceLoading,
  } = useLineupAdvice(week);

  const isLoading = leagueLoading || optimalLoading;

  // Build week options
  const weekOptions = Array.from({ length: currentWeek }, (_, i) => i + 1);

  // Derive swap suggestions from lineup advice
  const swapSuggestions =
    advice?.suggestions
      ?.filter((s) => s.action === "start")
      ?.map((suggestion) => {
        // Find the matching bench player in optimal data
        const benchPlayer = optimal?.bench?.find(
          (p) => p.id === suggestion.playerId,
        );
        // Find a starter at the same position who could be benched
        const starterToBench = optimal?.starters?.find(
          (p) => p.position === suggestion.position,
        );

        if (!benchPlayer || !starterToBench) return null;

        return {
          benchPlayer: {
            name: suggestion.playerName,
            position: suggestion.position,
            projectedPoints: benchPlayer.projectedPoints,
          },
          starter: {
            name: starterToBench.name,
            position: starterToBench.position,
            projectedPoints: starterToBench.projectedPoints,
          },
          reason: suggestion.reason,
        };
      })
      ?.filter(Boolean) ?? [];

  // Convert roster players to PlayerSlotData
  function toSlotData(
    player: {
      id: string;
      name: string;
      position: string;
      team: string;
      slot: string;
      projectedPoints: number;
      status?: string;
    },
  ): PlayerSlotData {
    // Find advice for this player
    const playerAdvice = advice?.suggestions?.find(
      (s) => s.playerId === player.id,
    );
    const confidence = playerAdvice?.confidence ?? undefined;

    return {
      id: player.id,
      name: player.name,
      position: player.position,
      team: player.team,
      slot: player.slot,
      projectedPoints: player.projectedPoints,
      compositeScore: confidence !== undefined ? Math.round(confidence * 100) : undefined,
      status: player.status,
      // These would come from a richer API response in a full implementation
      matchupGrade: undefined,
      boomProbability: undefined,
      bustProbability: undefined,
      snapCounts: undefined,
    };
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-50">Lineup</h1>
          <p className="mt-1 text-surface-400">
            Optimize your starting lineup with AI-driven recommendations
          </p>
        </div>

        {/* Week Selector */}
        <div className="flex items-center gap-2">
          <label
            htmlFor="week-select"
            className="text-sm font-medium text-surface-400"
          >
            Week
          </label>
          <select
            id="week-select"
            value={week}
            onChange={(e) => setSelectedWeek(Number(e.target.value))}
            className="rounded-lg border border-surface-700 bg-surface-800 px-3 py-1.5 text-sm text-surface-100 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          >
            {weekOptions.map((w) => (
              <option key={w} value={w}>
                Week {w}
                {w === currentWeek ? " (Current)" : ""}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex h-64 items-center justify-center">
          <LoadingSpinner size="lg" label="Analyzing your lineup..." />
        </div>
      )}

      {/* Error State */}
      {!isLoading && optimalError && (
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
            Please check your connection and try again
          </p>
        </div>
      )}

      {/* Loaded Content */}
      {!isLoading && !optimalError && optimal && (
        <>
          {/* Projected Total */}
          <div className="card flex items-center justify-between">
            <div>
              <p className="text-xs font-medium uppercase text-surface-500">
                Projected Total
              </p>
              <p className="text-3xl font-bold tabular-nums text-accent-400">
                {optimal.projectedTotal.toFixed(1)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-surface-500">
                Week {optimal.week}
              </p>
              <p className="text-sm text-surface-400">
                {optimal.starters.length} starters / {optimal.bench.length} bench
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

          {/* Advice reasoning */}
          {!adviceLoading && advice?.reasoning && (
            <div className="card border-primary-700/30 bg-primary-800/10">
              <div className="flex items-start gap-3">
                <svg
                  className="mt-0.5 h-5 w-5 flex-shrink-0 text-primary-300"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="16" x2="12" y2="12" />
                  <line x1="12" y1="8" x2="12.01" y2="8" />
                </svg>
                <div>
                  <p className="text-sm font-medium text-primary-200">
                    AI Analysis
                  </p>
                  <p className="mt-1 text-sm text-surface-300">
                    {advice.reasoning}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Starters Section */}
          <div className="space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-surface-400">
              Starters
            </h2>
            {optimal.starters.length === 0 ? (
              <EmptyState
                title="No starters"
                description="No starter data available for this week"
              />
            ) : (
              <div className="space-y-2">
                {optimal.starters.map((player) => (
                  <PlayerSlotCard
                    key={player.id}
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
            {optimal.bench.length === 0 ? (
              <EmptyState
                title="No bench players"
                description="No bench data available for this week"
              />
            ) : (
              <div className="space-y-2">
                {optimal.bench.map((player) => (
                  <PlayerSlotCard
                    key={player.id}
                    player={toSlotData(player)}
                  />
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {/* Empty State - no data at all */}
      {!isLoading && !optimalError && !optimal && (
        <EmptyState
          title="No lineup data"
          description="Sync your league to start getting lineup recommendations"
        />
      )}
    </div>
  );
}
