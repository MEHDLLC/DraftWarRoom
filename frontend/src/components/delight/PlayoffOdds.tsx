import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";

// ---------------------------------------------------------------------------
// Icons
// ---------------------------------------------------------------------------

function TrendUpIcon({ className }: { className?: string }) {
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
      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
      <polyline points="17 6 23 6 23 12" />
    </svg>
  );
}

function TrendDownIcon({ className }: { className?: string }) {
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
      <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
      <polyline points="17 18 23 18 23 12" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// PlayoffOdds
// ---------------------------------------------------------------------------

interface PlayoffOddsProps {
  probability: number; // 0–100
  previousProbability?: number; // 0–100
}

export default function PlayoffOdds({
  probability,
  previousProbability,
}: PlayoffOddsProps) {
  const clamped = Math.max(0, Math.min(100, probability));
  const remaining = 100 - clamped;

  const data = [
    { name: "Chance", value: clamped },
    { name: "Remaining", value: remaining },
  ];

  // Determine color based on probability
  const getColor = (pct: number) => {
    if (pct >= 70) return { main: "#38a169", bg: "text-success-400" }; // success
    if (pct >= 40) return { main: "#d69e2e", bg: "text-accent-400" }; // accent
    return { main: "#e53e3e", bg: "text-danger-400" }; // danger
  };

  const color = getColor(clamped);

  // Trend calculation
  const hasTrend =
    previousProbability !== undefined && previousProbability !== probability;
  const trendDiff = hasTrend ? probability - previousProbability! : 0;
  const trendUp = trendDiff > 0;

  return (
    <div className="card overflow-hidden">
      {/* Accent top bar */}
      <div
        className="h-1 w-full"
        style={{ backgroundColor: color.main }}
      />

      <div className="p-5">
        {/* Header */}
        <h3 className="mb-4 text-base font-semibold text-surface-100">
          Playoff Odds
        </h3>

        {/* Donut chart with center number */}
        <div className="relative mx-auto mb-4 h-44 w-44">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={75}
                startAngle={90}
                endAngle={-270}
                dataKey="value"
                stroke="none"
                animationDuration={800}
              >
                <Cell fill={color.main} />
                <Cell fill="#1e293b" />
              </Pie>
            </PieChart>
          </ResponsiveContainer>

          {/* Center content */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span
              className={[
                "text-3xl font-extrabold",
                color.bg,
              ].join(" ")}
            >
              {clamped}%
            </span>
            <span className="text-xs text-surface-400">probability</span>
          </div>
        </div>

        {/* Trend indicator */}
        {hasTrend && (
          <div className="flex items-center justify-center gap-2">
            {trendUp ? (
              <TrendUpIcon className="h-4 w-4 text-success-400" />
            ) : (
              <TrendDownIcon className="h-4 w-4 text-danger-400" />
            )}
            <span
              className={[
                "text-sm font-semibold",
                trendUp ? "text-success-400" : "text-danger-400",
              ].join(" ")}
            >
              {trendUp ? "+" : ""}
              {trendDiff.toFixed(1)}%
            </span>
            <span className="text-xs text-surface-500">from last week</span>
          </div>
        )}

        {/* Status message */}
        <div className="mt-4 text-center">
          <p className="text-sm text-surface-300">
            {clamped >= 90
              ? "Almost a lock! Keep doing what you're doing."
              : clamped >= 70
                ? "Looking strong. Stay the course."
                : clamped >= 50
                  ? "On the bubble. Every win counts."
                  : clamped >= 25
                    ? "Uphill battle. Time to make some moves."
                    : "Long shot. You'll need a miracle run."}
          </p>
        </div>
      </div>
    </div>
  );
}
