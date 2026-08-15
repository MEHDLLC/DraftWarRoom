interface RecordCardProps {
  record: { wins: number; losses: number; ties: number };
  standing: number;
  pointsRank: number;
  recentTrend: Array<"W" | "L">;
}

export default function RecordCard({
  record,
  standing,
  pointsRank,
  recentTrend,
}: RecordCardProps) {
  const totalGames = record.wins + record.losses + record.ties;
  const winPct = totalGames > 0 ? (record.wins / totalGames) * 100 : 0;

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-surface-400">
          Season Record
        </h2>
        <span className="rounded-full bg-primary-800/60 px-3 py-0.5 text-xs font-medium text-primary-200">
          {winPct.toFixed(0)}% Win Rate
        </span>
      </div>

      {/* Main Record */}
      <div className="flex items-baseline gap-1">
        <span className="text-4xl font-bold tabular-nums text-surface-50">
          {record.wins}
        </span>
        <span className="text-2xl text-surface-500">-</span>
        <span className="text-4xl font-bold tabular-nums text-surface-50">
          {record.losses}
        </span>
        {record.ties > 0 && (
          <>
            <span className="text-2xl text-surface-500">-</span>
            <span className="text-4xl font-bold tabular-nums text-surface-50">
              {record.ties}
            </span>
          </>
        )}
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-surface-900/60 px-3 py-2">
          <p className="text-xs text-surface-500">Standing</p>
          <p className="text-lg font-semibold text-surface-100">
            {standing}
            <span className="text-xs text-surface-400">
              {standing === 1
                ? "st"
                : standing === 2
                  ? "nd"
                  : standing === 3
                    ? "rd"
                    : "th"}
            </span>
          </p>
        </div>
        <div className="rounded-lg bg-surface-900/60 px-3 py-2">
          <p className="text-xs text-surface-500">Points Rank</p>
          <p className="text-lg font-semibold text-surface-100">
            {pointsRank}
            <span className="text-xs text-surface-400">
              {pointsRank === 1
                ? "st"
                : pointsRank === 2
                  ? "nd"
                  : pointsRank === 3
                    ? "rd"
                    : "th"}
            </span>
          </p>
        </div>
      </div>

      {/* Recent Trend */}
      {recentTrend.length > 0 && (
        <div>
          <p className="mb-2 text-xs text-surface-500">Recent</p>
          <div className="flex gap-1.5">
            {recentTrend.map((result, idx) => (
              <span
                key={idx}
                className={[
                  "flex h-7 w-7 items-center justify-center rounded-md text-xs font-bold",
                  result === "W"
                    ? "bg-success-400/20 text-success-400"
                    : "bg-danger-400/20 text-danger-400",
                ].join(" ")}
              >
                {result}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
