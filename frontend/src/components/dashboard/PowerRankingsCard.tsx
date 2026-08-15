import type { PowerRanking } from "@/api/client";
import { useLeague } from "@/context/LeagueContext";
import { usePowerRankings } from "@/hooks/useDashboard";
import LoadingSpinner from "@/components/shared/LoadingSpinner";

function TrendArrow({ trend }: { trend: number }) {
  if (trend === 0) {
    return (
      <span className="text-xs text-surface-500" title="No change">
        --
      </span>
    );
  }

  if (trend > 0) {
    return (
      <span
        className="inline-flex items-center gap-0.5 text-xs font-medium text-success-400"
        title={`Up ${trend}`}
      >
        <svg
          className="h-3 w-3"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="18 15 12 9 6 15" />
        </svg>
        {Math.abs(trend)}
      </span>
    );
  }

  return (
    <span
      className="inline-flex items-center gap-0.5 text-xs font-medium text-danger-400"
      title={`Down ${Math.abs(trend)}`}
    >
      <svg
        className="h-3 w-3"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <polyline points="6 9 12 15 18 9" />
      </svg>
      {Math.abs(trend)}
    </span>
  );
}

function RankBadge({ rank }: { rank: number }) {
  const colors =
    rank === 1
      ? "bg-accent-500/20 text-accent-400 border-accent-500/30"
      : rank <= 3
        ? "bg-primary-800/40 text-primary-200 border-primary-700/50"
        : "bg-surface-700/40 text-surface-400 border-surface-700/50";

  return (
    <span
      className={[
        "flex h-7 w-7 items-center justify-center rounded-md border text-xs font-bold",
        colors,
      ].join(" ")}
    >
      {rank}
    </span>
  );
}

export default function PowerRankingsCard() {
  const { userTeam } = useLeague();
  const { data: rankings, isLoading, isError } = usePowerRankings();

  if (isLoading) {
    return (
      <div className="card">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-surface-400">
          Power Rankings
        </h2>
        <div className="flex h-48 items-center justify-center">
          <LoadingSpinner size="md" />
        </div>
      </div>
    );
  }

  if (isError || !rankings) {
    return (
      <div className="card">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-surface-400">
          Power Rankings
        </h2>
        <div className="flex h-48 items-center justify-center">
          <p className="text-sm text-surface-500">
            Unable to load power rankings
          </p>
        </div>
      </div>
    );
  }

  const sorted = [...rankings].sort((a, b) => a.rank - b.rank);

  return (
    <div className="card">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-surface-400">
        Power Rankings
      </h2>

      <div className="space-y-1">
        {sorted.map((team: PowerRanking) => {
          const isUser = team.teamId === userTeam?.id;

          return (
            <div
              key={team.teamId}
              className={[
                "flex items-center gap-3 rounded-lg px-3 py-2 transition-colors",
                isUser
                  ? "bg-primary-800/30 ring-1 ring-primary-700/50"
                  : "hover:bg-surface-700/30",
              ].join(" ")}
            >
              <RankBadge rank={team.rank} />

              <div className="min-w-0 flex-1">
                <p
                  className={[
                    "truncate text-sm font-medium",
                    isUser ? "text-accent-400" : "text-surface-200",
                  ].join(" ")}
                >
                  {team.teamName}
                  {isUser && (
                    <span className="ml-1.5 text-xs text-accent-500/70">
                      (You)
                    </span>
                  )}
                </p>
              </div>

              <div className="flex items-center gap-4">
                <span className="w-12 text-right text-sm font-semibold tabular-nums text-surface-300">
                  {team.score.toFixed(1)}
                </span>
                <div className="w-8">
                  <TrendArrow trend={team.trend} />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
