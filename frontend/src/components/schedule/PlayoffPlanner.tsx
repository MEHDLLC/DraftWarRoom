import { usePlayoffSchedule } from "@/hooks/useSchedule";
import { useExplainMode } from "@/context/ExplainModeContext";
import LoadingSpinner from "@/components/shared/LoadingSpinner";
import EmptyState from "@/components/shared/EmptyState";

// ── Trophy icon ────────────────────────────────────────────────────────
function TrophyIcon({ className }: { className?: string }) {
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
      <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" />
      <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18" />
      <path d="M4 22h16" />
      <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22" />
      <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22" />
      <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z" />
    </svg>
  );
}

// ── Readiness gauge ────────────────────────────────────────────────────
function ReadinessGauge({ probability }: { probability: number }) {
  const percent = Math.round(probability * 100);

  let color: string;
  let label: string;
  if (percent >= 70) {
    color = "text-success-400";
    label = "Strong";
  } else if (percent >= 40) {
    color = "text-accent-400";
    label = "Competitive";
  } else {
    color = "text-danger-400";
    label = "At Risk";
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className={`relative flex h-24 w-24 items-center justify-center rounded-full border-4 ${color}`}
        style={{
          borderColor: "currentColor",
          background: `conic-gradient(currentColor ${percent * 3.6}deg, rgba(51,65,85,0.3) 0deg)`,
        }}
      >
        <div className="flex h-[76px] w-[76px] flex-col items-center justify-center rounded-full bg-surface-800">
          <span className={`text-2xl font-bold ${color}`}>{percent}%</span>
        </div>
      </div>
      <span className={`text-sm font-semibold ${color}`}>{label}</span>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────
export default function PlayoffPlanner() {
  const { explainMode } = useExplainMode();
  const { data: playoffData, isLoading, isError, error, refetch } =
    usePlayoffSchedule();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <LoadingSpinner size="lg" label="Analyzing playoff scenarios..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-danger-400/30 bg-danger-400/5 p-6 text-center">
        <p className="text-sm text-danger-300">
          {(error as Error)?.message ?? "Failed to load playoff data."}
        </p>
        <button onClick={() => refetch()} className="btn-primary mt-4">
          Retry
        </button>
      </div>
    );
  }

  if (!playoffData) {
    return (
      <EmptyState
        title="No playoff data"
        description="Playoff scenarios are not yet available."
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Playoff readiness score ── */}
      <div className="bg-surface-800 rounded-xl border border-surface-700 p-6">
        <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start sm:gap-8">
          <ReadinessGauge probability={playoffData.playoffProbability} />

          <div className="flex-1 space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-surface-100">
                Playoff Readiness
              </h3>
              <p className="mt-1 text-sm text-surface-400">
                Current Standing:{" "}
                <span className="font-semibold text-accent-400">
                  #{playoffData.currentStanding}
                </span>
              </p>
            </div>

            {/* Scenarios */}
            <div className="grid gap-3 sm:grid-cols-2">
              {/* Clinch scenario */}
              <div className="rounded-lg border border-success-400/20 bg-success-400/5 p-3">
                <div className="flex items-center gap-2">
                  <TrophyIcon className="h-4 w-4 text-success-400" />
                  <h4 className="text-xs font-semibold text-success-400 uppercase tracking-wider">
                    Clinch
                  </h4>
                </div>
                <p className="mt-1.5 text-sm text-surface-300">
                  {playoffData.clinchScenario ?? "Not yet determined"}
                </p>
              </div>

              {/* Elimination scenario */}
              <div className="rounded-lg border border-danger-400/20 bg-danger-400/5 p-3">
                <div className="flex items-center gap-2">
                  <svg
                    className="h-4 w-4 text-danger-400"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                    <line x1="12" y1="9" x2="12" y2="13" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                  <h4 className="text-xs font-semibold text-danger-400 uppercase tracking-wider">
                    Elimination
                  </h4>
                </div>
                <p className="mt-1.5 text-sm text-surface-300">
                  {playoffData.eliminationScenario ?? "Not yet determined"}
                </p>
              </div>
            </div>

            {/* Additional explanation */}
            {explainMode && (
              <div className="rounded-lg bg-primary-800/20 px-3 py-2">
                <p className="text-xs leading-relaxed text-surface-300">
                  Playoff probability is calculated based on current standings,
                  remaining schedule strength, projected weekly scores, and
                  simulation of remaining games. A higher percentage means a
                  more favorable path to the postseason.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
