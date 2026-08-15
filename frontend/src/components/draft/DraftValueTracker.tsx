import { useDraftValueTracker } from "@/hooks/useDraft";
import { useExplainMode } from "@/context/ExplainModeContext";
import type { DraftPickValue } from "@/api/client";
import LoadingSpinner from "@/components/shared/LoadingSpinner";
import EmptyState from "@/components/shared/EmptyState";

// ── Value badge ────────────────────────────────────────────────────────
function ValueBadge({ value }: { value: number }) {
  const isPositive = value > 0;
  const isNeutral = value === 0;

  let colorClass: string;
  if (isNeutral) {
    colorClass = "text-surface-400 bg-surface-700";
  } else if (isPositive) {
    colorClass = "text-success-400 bg-success-400/10";
  } else {
    colorClass = "text-danger-400 bg-danger-400/10";
  }

  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-bold ${colorClass}`}
    >
      {isPositive ? "+" : ""}
      {value.toFixed(1)}
    </span>
  );
}

// ── Summary stat card ──────────────────────────────────────────────────
function StatCard({
  label,
  value,
  subtext,
  colorClass,
}: {
  label: string;
  value: string;
  subtext?: string;
  colorClass: string;
}) {
  return (
    <div className="bg-surface-800 rounded-xl border border-surface-700 p-4">
      <p className="text-xs font-medium text-surface-500 uppercase tracking-wider">
        {label}
      </p>
      <p className={`mt-1 text-xl font-bold ${colorClass}`}>{value}</p>
      {subtext && (
        <p className="mt-0.5 text-xs text-surface-400">{subtext}</p>
      )}
    </div>
  );
}

// ── Position badge ─────────────────────────────────────────────────────
const positionColors: Record<string, string> = {
  QB: "text-pink-300",
  RB: "text-emerald-300",
  WR: "text-sky-300",
  TE: "text-orange-300",
  K: "text-purple-300",
  DEF: "text-yellow-300",
};

// ── Main component ─────────────────────────────────────────────────────
export default function DraftValueTracker() {
  const { explainMode } = useExplainMode();
  const { data: tracker, isLoading, isError, error, refetch } =
    useDraftValueTracker();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <LoadingSpinner size="lg" label="Loading draft data..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-danger-400/30 bg-danger-400/5 p-6 text-center">
        <p className="text-sm text-danger-300">
          {(error as Error)?.message ?? "Failed to load draft value data."}
        </p>
        <button onClick={() => refetch()} className="btn-primary mt-4">
          Retry
        </button>
      </div>
    );
  }

  if (!tracker || tracker.picks.length === 0) {
    return (
      <EmptyState
        title="No draft picks"
        description="Draft data will appear here once the draft begins."
      />
    );
  }

  // Compute summary stats
  const totalValue = tracker.picks.reduce((sum, p) => sum + p.value, 0);
  const bestPick = tracker.picks.reduce(
    (best, p) => (p.value > best.value ? p : best),
    tracker.picks[0]
  );
  const worstPick = tracker.picks.reduce(
    (worst, p) => (p.value < worst.value ? p : worst),
    tracker.picks[0]
  );

  return (
    <div className="space-y-6">
      {/* ── Summary stats ── */}
      <div className="grid gap-3 sm:grid-cols-3">
        <StatCard
          label="Total Value"
          value={`${totalValue >= 0 ? "+" : ""}${totalValue.toFixed(1)}`}
          colorClass={totalValue >= 0 ? "text-success-400" : "text-danger-400"}
        />
        <StatCard
          label="Best Pick"
          value={bestPick.player.name}
          subtext={`+${bestPick.value.toFixed(1)} vs ADP (Pick ${bestPick.pickNumber})`}
          colorClass="text-success-400"
        />
        <StatCard
          label="Worst Pick"
          value={worstPick.player.name}
          subtext={`${worstPick.value.toFixed(1)} vs ADP (Pick ${worstPick.pickNumber})`}
          colorClass="text-danger-400"
        />
      </div>

      {/* ── Picks table ── */}
      <div className="bg-surface-800 rounded-xl border border-surface-700 overflow-hidden">
        {/* Table header */}
        <div className="grid grid-cols-12 gap-2 border-b border-surface-700 bg-surface-900/50 px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-surface-500">
          <div className="col-span-1">Rd</div>
          <div className="col-span-1">Pick</div>
          <div className="col-span-4 sm:col-span-5">Player</div>
          <div className="col-span-2 text-center">ADP</div>
          <div className="col-span-2 text-center">Pick #</div>
          <div className="col-span-2 sm:col-span-1 text-right">Value</div>
        </div>

        {/* Table rows */}
        {tracker.picks.map((pick: DraftPickValue, idx: number) => {
          const round = Math.floor((pick.pickNumber - 1) / 12) + 1;
          const posColor = positionColors[pick.player.position] ?? "text-surface-300";

          return (
            <div
              key={idx}
              className={[
                "grid grid-cols-12 gap-2 items-center px-4 py-2.5 text-sm border-b border-surface-700/50 last:border-b-0 transition-colors hover:bg-surface-700/30",
                pick.value > 0 ? "bg-success-400/[0.02]" : pick.value < 0 ? "bg-danger-400/[0.02]" : "",
              ].join(" ")}
            >
              <div className="col-span-1 text-xs text-surface-500">{round}</div>
              <div className="col-span-1 text-xs text-surface-400">
                {pick.pickNumber}
              </div>
              <div className="col-span-4 sm:col-span-5 flex items-center gap-2 min-w-0">
                <span className={`text-xs font-medium ${posColor}`}>
                  {pick.player.position}
                </span>
                <span className="truncate font-medium text-surface-100">
                  {pick.player.name}
                </span>
                <span className="hidden text-xs text-surface-500 sm:inline">
                  {pick.player.team}
                </span>
              </div>
              <div className="col-span-2 text-center text-xs text-surface-400">
                {pick.adp.toFixed(1)}
              </div>
              <div className="col-span-2 text-center text-xs text-surface-400">
                {pick.pickNumber}
              </div>
              <div className="col-span-2 sm:col-span-1 flex justify-end">
                <ValueBadge value={pick.value} />
              </div>
            </div>
          );
        })}
      </div>

      {/* ── AI Recommendations ── */}
      {explainMode && tracker.recommendations.length > 0 && (
        <div className="bg-surface-800 rounded-xl border border-surface-700 p-4">
          <h3 className="text-sm font-semibold text-surface-200">
            Draft Insights
          </h3>
          <ul className="mt-2 space-y-1.5">
            {tracker.recommendations.map((rec, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 text-xs text-surface-300"
              >
                <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent-400" />
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
