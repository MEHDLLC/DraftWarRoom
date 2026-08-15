import { useState } from "react";
import MatchupPreview from "@/components/matchup/MatchupPreview";
import { useMatchupByWeek, useMatchupAnalysis } from "@/hooks/useMatchups";
import { useLeague } from "@/context/LeagueContext";
import { useExplainMode } from "@/context/ExplainModeContext";
import LoadingSpinner from "@/components/shared/LoadingSpinner";
import EmptyState from "@/components/shared/EmptyState";

// ── Chevron icons ──────────────────────────────────────────────────────
function ChevronLeftIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="15 18 9 12 15 6" />
    </svg>
  );
}

function ChevronRightIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="9 18 15 12 9 6" />
    </svg>
  );
}

// ── Page component ─────────────────────────────────────────────────────
export default function MatchupPage() {
  const { league } = useLeague();
  const { explainMode } = useExplainMode();
  const currentWeek = league?.week ?? 1;
  const [selectedWeek, setSelectedWeek] = useState(currentWeek);

  const {
    data: matchup,
    isLoading,
    isError,
    error,
    refetch,
  } = useMatchupByWeek(selectedWeek);

  const { data: analysis } = useMatchupAnalysis(selectedWeek);

  const maxWeek = 18;

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div>
        <h1 className="text-2xl font-bold text-surface-50">Matchup</h1>
        <p className="mt-1 text-surface-400">
          Analyze your weekly matchup and win probability
        </p>
      </div>

      {/* ── Week selector ── */}
      <div className="flex items-center justify-center gap-3">
        <button
          onClick={() => setSelectedWeek((w) => Math.max(1, w - 1))}
          disabled={selectedWeek <= 1}
          className="rounded-lg p-2 text-surface-400 transition-colors hover:bg-surface-800 hover:text-surface-100 disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Previous week"
        >
          <ChevronLeftIcon className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-2">
          <span className="text-lg font-bold text-surface-100">
            Week {selectedWeek}
          </span>
          {selectedWeek === currentWeek && (
            <span className="rounded bg-accent-500/20 px-1.5 py-0.5 text-[10px] font-bold text-accent-400 uppercase">
              Current
            </span>
          )}
        </div>

        <button
          onClick={() => setSelectedWeek((w) => Math.min(maxWeek, w + 1))}
          disabled={selectedWeek >= maxWeek}
          className="rounded-lg p-2 text-surface-400 transition-colors hover:bg-surface-800 hover:text-surface-100 disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Next week"
        >
          <ChevronRightIcon className="h-5 w-5" />
        </button>
      </div>

      {/* ── Loading ── */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <LoadingSpinner size="lg" label="Loading matchup data..." />
        </div>
      )}

      {/* ── Error ── */}
      {isError && (
        <div className="rounded-xl border border-danger-400/30 bg-danger-400/5 p-6 text-center">
          <p className="text-sm text-danger-300">
            {(error as Error)?.message ?? "Failed to load matchup."}
          </p>
          <button onClick={() => refetch()} className="btn-primary mt-4">
            Retry
          </button>
        </div>
      )}

      {/* ── Empty ── */}
      {!isLoading && !isError && !matchup && (
        <EmptyState
          title="No matchup data"
          description={`No matchup information available for Week ${selectedWeek}.`}
        />
      )}

      {/* ── Matchup preview ── */}
      {matchup && (
        <div className="space-y-6">
          <MatchupPreview matchup={matchup} />

          {/* ── Analysis section ── */}
          {analysis && (
            <div className="bg-surface-800 rounded-xl border border-surface-700 p-5">
              <h3 className="text-sm font-semibold text-surface-200">
                Matchup Analysis
              </h3>

              {/* Key players */}
              {analysis.keyPlayers.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-medium text-surface-500 uppercase tracking-wider">
                    Key Players to Watch
                  </p>
                  <div className="mt-1.5 flex flex-wrap gap-2">
                    {analysis.keyPlayers.map((name, idx) => (
                      <span
                        key={idx}
                        className="rounded-md border border-accent-400/20 bg-accent-400/5 px-2 py-1 text-xs font-medium text-accent-300"
                      >
                        {name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Analysis text */}
              {explainMode && analysis.analysis && (
                <div className="mt-3 rounded-lg bg-primary-800/20 px-3 py-2">
                  <p className="text-xs leading-relaxed text-surface-300">
                    {analysis.analysis}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
