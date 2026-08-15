import { useQuery } from "@tanstack/react-query";
import { lineupApi, type OptimalLineup, type RosterPlayer } from "@/api/client";
import LoadingSpinner from "@/components/shared/LoadingSpinner";

// ---------------------------------------------------------------------------
// Icons
// ---------------------------------------------------------------------------

function TargetIcon({ className }: { className?: string }) {
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
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="6" />
      <circle cx="12" cy="12" r="2" />
    </svg>
  );
}

function ArrowUpIcon({ className }: { className?: string }) {
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
      <line x1="12" y1="19" x2="12" y2="5" />
      <polyline points="5 12 12 5 19 12" />
    </svg>
  );
}

function ArrowDownIcon({ className }: { className?: string }) {
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
      <line x1="12" y1="5" x2="12" y2="19" />
      <polyline points="19 12 12 19 5 12" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// OptimalLineupCard
// ---------------------------------------------------------------------------

interface OptimalLineupCardProps {
  week: number;
  actualScore?: number;
  actualStarters?: RosterPlayer[];
}

export default function OptimalLineupCard({
  week,
  actualScore,
  actualStarters,
}: OptimalLineupCardProps) {
  const {
    data: optimal,
    isLoading,
    isError,
  } = useQuery<OptimalLineup>({
    queryKey: ["lineup", "optimal", week],
    queryFn: () => lineupApi.getOptimal(week),
    staleTime: 1000 * 60 * 5,
    retry: 2,
  });

  if (isLoading) {
    return (
      <div className="card flex items-center justify-center py-12">
        <LoadingSpinner size="md" label="Calculating optimal lineup..." />
      </div>
    );
  }

  if (isError || !optimal) {
    return (
      <div className="card py-8 text-center">
        <p className="text-sm text-surface-400">
          Unable to calculate optimal lineup for this week.
        </p>
      </div>
    );
  }

  const optimalTotal = optimal.projectedTotal;
  const yourScore = actualScore ?? 0;
  const pointsLeftOnBench = optimalTotal - yourScore;
  const efficiency =
    optimalTotal > 0 ? Math.round((yourScore / optimalTotal) * 100) : 100;

  // Build a map of optimal starter IDs for comparison
  const optimalStarterIds = new Set(optimal.starters.map((p) => p.id));
  const actualStarterIds = new Set(
    actualStarters?.map((p) => p.id) ?? [],
  );

  return (
    <div className="card overflow-hidden">
      {/* Accent top bar */}
      <div
        className={[
          "h-1 w-full",
          pointsLeftOnBench > 10
            ? "bg-danger-400"
            : pointsLeftOnBench > 0
              ? "bg-accent-500"
              : "bg-success-400",
        ].join(" ")}
      />

      <div className="p-5">
        {/* Header */}
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-800/50">
            <TargetIcon className="h-5 w-5 text-accent-400" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-surface-100">
              Optimal Lineup - Week {week}
            </h3>
            <p className="text-xs text-surface-400">
              {efficiency}% lineup efficiency
            </p>
          </div>
        </div>

        {/* Score comparison */}
        <div className="mb-5 flex items-center justify-between rounded-xl bg-surface-900/60 p-4">
          <div className="text-center">
            <p className="text-xs font-medium text-surface-400">You Scored</p>
            <p className="mt-1 text-2xl font-bold text-surface-100">
              {yourScore.toFixed(1)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs font-medium text-surface-400">
              Optimal Was
            </p>
            <p className="mt-1 text-2xl font-bold text-accent-400">
              {optimalTotal.toFixed(1)}
            </p>
          </div>
        </div>

        {/* Points left on bench */}
        {pointsLeftOnBench > 0 && (
          <div className="mb-5 text-center">
            <p className="text-xs font-medium text-surface-400">
              Points Left on Bench
            </p>
            <p className="mt-1 text-3xl font-extrabold text-danger-400">
              {pointsLeftOnBench.toFixed(1)}
            </p>
          </div>
        )}

        {/* Optimal starters list */}
        <div className="space-y-1">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-surface-400">
            Optimal Starters
          </p>
          {optimal.starters.map((player) => {
            const wasStarted = actualStarterIds.has(player.id);
            return (
              <div
                key={player.id}
                className="flex items-center justify-between rounded-lg px-3 py-2 text-sm hover:bg-surface-800/50"
              >
                <div className="flex items-center gap-2">
                  {wasStarted ? (
                    <ArrowUpIcon className="h-3.5 w-3.5 text-success-400" />
                  ) : (
                    <ArrowDownIcon className="h-3.5 w-3.5 text-danger-400" />
                  )}
                  <span
                    className={[
                      "font-medium",
                      wasStarted ? "text-surface-100" : "text-danger-300",
                    ].join(" ")}
                  >
                    {player.name}
                  </span>
                  <span className="rounded bg-surface-700/50 px-1.5 py-0.5 text-xs text-surface-400">
                    {player.position}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-surface-200">
                    {player.projectedPoints.toFixed(1)}
                  </span>
                  {!wasStarted && (
                    <span className="rounded-full bg-danger-400/15 px-2 py-0.5 text-xs font-medium text-danger-400">
                      Benched
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Bench (those who should not have started) */}
        {actualStarters && actualStarters.length > 0 && (
          <div className="mt-4 space-y-1">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-surface-400">
              Should Have Benched
            </p>
            {actualStarters
              .filter((p) => !optimalStarterIds.has(p.id))
              .map((player) => (
                <div
                  key={player.id}
                  className="flex items-center justify-between rounded-lg px-3 py-2 text-sm hover:bg-surface-800/50"
                >
                  <div className="flex items-center gap-2">
                    <ArrowDownIcon className="h-3.5 w-3.5 text-surface-500" />
                    <span className="font-medium text-surface-400">
                      {player.name}
                    </span>
                    <span className="rounded bg-surface-700/50 px-1.5 py-0.5 text-xs text-surface-400">
                      {player.position}
                    </span>
                  </div>
                  <span className="text-sm text-surface-400">
                    {player.projectedPoints.toFixed(1)}
                  </span>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
