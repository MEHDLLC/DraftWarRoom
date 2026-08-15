import { useStrengthOfSchedule } from "@/hooks/useSchedule";
import LoadingSpinner from "@/components/shared/LoadingSpinner";
import EmptyState from "@/components/shared/EmptyState";

// ── Difficulty color mapping ───────────────────────────────────────────
function difficultyColor(value: number): string {
  // value: 0 (easy) to 10 (hard)
  if (value <= 2) return "bg-success-400 text-surface-900";
  if (value <= 4) return "bg-success-400/60 text-surface-900";
  if (value <= 5) return "bg-accent-400/70 text-surface-900";
  if (value <= 7) return "bg-orange-400/70 text-surface-900";
  if (value <= 8) return "bg-danger-400/70 text-white";
  return "bg-danger-400 text-white";
}

function difficultyLabel(value: number): string {
  if (value <= 2) return "Easy";
  if (value <= 4) return "Favorable";
  if (value <= 6) return "Average";
  if (value <= 8) return "Tough";
  return "Hard";
}

export default function StrengthOfSchedule() {
  const { data: sosData, isLoading, isError, error, refetch } =
    useStrengthOfSchedule();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <LoadingSpinner size="lg" label="Calculating schedule strength..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-danger-400/30 bg-danger-400/5 p-6 text-center">
        <p className="text-sm text-danger-300">
          {(error as Error)?.message ?? "Failed to load schedule data."}
        </p>
        <button onClick={() => refetch()} className="btn-primary mt-4">
          Retry
        </button>
      </div>
    );
  }

  if (!sosData || sosData.length === 0) {
    return (
      <EmptyState
        title="No schedule data"
        description="Schedule strength data is not yet available."
      />
    );
  }

  // Determine the number of weeks from the data
  const maxWeeks = Math.max(...sosData.map((s) => s.weeklyDifficulty.length));
  const weekNumbers = Array.from({ length: maxWeeks }, (_, i) => i + 1);

  return (
    <div className="space-y-4">
      {/* Legend */}
      <div className="flex flex-wrap items-center gap-3 text-xs text-surface-400">
        <span className="font-medium">Difficulty:</span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-3 w-3 rounded bg-success-400" /> Easy
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-3 w-3 rounded bg-accent-400/70" /> Avg
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-3 w-3 rounded bg-danger-400" /> Hard
        </span>
      </div>

      {/* Heatmap grid */}
      <div className="overflow-x-auto">
        <div className="min-w-[600px]">
          {/* Header row: week numbers */}
          <div className="flex">
            <div className="w-36 flex-shrink-0 px-2 py-1.5 text-xs font-semibold text-surface-400">
              Team
            </div>
            {weekNumbers.map((week) => (
              <div
                key={week}
                className="w-12 flex-shrink-0 px-1 py-1.5 text-center text-xs font-medium text-surface-500"
              >
                W{week}
              </div>
            ))}
            <div className="w-16 flex-shrink-0 px-2 py-1.5 text-center text-xs font-semibold text-surface-400">
              SOS
            </div>
          </div>

          {/* Data rows */}
          {sosData
            .sort((a, b) => a.rank - b.rank)
            .map((team) => (
              <div
                key={team.teamId}
                className="flex items-center border-t border-surface-700/50"
              >
                {/* Team name */}
                <div className="w-36 flex-shrink-0 px-2 py-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-surface-500">
                      #{team.rank}
                    </span>
                    <span className="truncate text-xs font-medium text-surface-200">
                      {team.teamName}
                    </span>
                  </div>
                </div>

                {/* Weekly difficulty cells */}
                {weekNumbers.map((week) => {
                  const difficulty = team.weeklyDifficulty[week - 1];
                  if (difficulty === undefined) {
                    return (
                      <div
                        key={week}
                        className="flex h-8 w-12 flex-shrink-0 items-center justify-center"
                      >
                        <span className="text-[10px] text-surface-600">--</span>
                      </div>
                    );
                  }
                  return (
                    <div
                      key={week}
                      className="flex h-8 w-12 flex-shrink-0 items-center justify-center px-0.5"
                    >
                      <span
                        className={`flex h-7 w-full items-center justify-center rounded text-[10px] font-bold ${difficultyColor(
                          difficulty
                        )}`}
                        title={`Week ${week}: ${difficultyLabel(difficulty)} (${difficulty.toFixed(1)})`}
                      >
                        {difficulty.toFixed(0)}
                      </span>
                    </div>
                  );
                })}

                {/* Overall SOS */}
                <div className="flex h-8 w-16 flex-shrink-0 items-center justify-center px-1">
                  <span
                    className={`flex h-7 w-full items-center justify-center rounded text-xs font-bold ${difficultyColor(
                      team.remainingSos
                    )}`}
                  >
                    {team.remainingSos.toFixed(1)}
                  </span>
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
