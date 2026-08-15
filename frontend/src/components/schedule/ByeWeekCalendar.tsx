import { useByeWeeks } from "@/hooks/useSchedule";
import { useLeague } from "@/context/LeagueContext";
import LoadingSpinner from "@/components/shared/LoadingSpinner";
import EmptyState from "@/components/shared/EmptyState";

// ── Alert icon ─────────────────────────────────────────────────────────
function AlertIcon({ className }: { className?: string }) {
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
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  );
}

// ── Severity helpers ───────────────────────────────────────────────────
function getByeSeverity(impactCount: number): {
  border: string;
  bg: string;
  text: string;
  label: string;
} {
  if (impactCount >= 3) {
    return {
      border: "border-danger-400/40",
      bg: "bg-danger-400/10",
      text: "text-danger-400",
      label: "Critical",
    };
  }
  if (impactCount === 2) {
    return {
      border: "border-accent-400/30",
      bg: "bg-accent-400/5",
      text: "text-accent-400",
      label: "Caution",
    };
  }
  return {
    border: "border-surface-700",
    bg: "bg-surface-800",
    text: "text-surface-400",
    label: "Manageable",
  };
}

export default function ByeWeekCalendar() {
  const { league } = useLeague();
  const { data: byeWeeks, isLoading, isError, error, refetch } = useByeWeeks();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <LoadingSpinner size="lg" label="Loading bye week schedule..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-danger-400/30 bg-danger-400/5 p-6 text-center">
        <p className="text-sm text-danger-300">
          {(error as Error)?.message ?? "Failed to load bye week data."}
        </p>
        <button onClick={() => refetch()} className="btn-primary mt-4">
          Retry
        </button>
      </div>
    );
  }

  if (!byeWeeks || byeWeeks.length === 0) {
    return (
      <EmptyState
        title="No bye week data"
        description="Bye week information is not yet available."
      />
    );
  }

  const currentWeek = league?.week ?? 1;

  return (
    <div className="space-y-4">
      {/* ── Summary alert for multi-bye weeks ── */}
      {(() => {
        const criticalWeeks = byeWeeks.filter(
          (bw) => bw.rosterImpact.length >= 2
        );
        if (criticalWeeks.length === 0) return null;
        return (
          <div className="rounded-xl border border-accent-400/30 bg-accent-400/5 p-4">
            <div className="flex items-start gap-2">
              <AlertIcon className="mt-0.5 h-4 w-4 flex-shrink-0 text-accent-400" />
              <div>
                <p className="text-sm font-medium text-accent-300">
                  {criticalWeeks.length} week{criticalWeeks.length > 1 ? "s" : ""} with
                  multiple starters on bye
                </p>
                <p className="mt-0.5 text-xs text-surface-400">
                  Plan ahead for weeks{" "}
                  {criticalWeeks.map((w) => w.week).join(", ")} to avoid lineup
                  gaps.
                </p>
              </div>
            </div>
          </div>
        );
      })()}

      {/* ── Calendar grid ── */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {byeWeeks.map((bw) => {
          const severity = getByeSeverity(bw.rosterImpact.length);
          const isPast = bw.week < currentWeek;
          const isCurrent = bw.week === currentWeek;

          return (
            <div
              key={bw.week}
              className={[
                "rounded-xl border p-4 transition-colors",
                severity.border,
                severity.bg,
                isPast ? "opacity-50" : "",
              ].join(" ")}
            >
              {/* Week header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-surface-100">
                    Week {bw.week}
                  </span>
                  {isCurrent && (
                    <span className="rounded bg-accent-500/20 px-1.5 py-0.5 text-[10px] font-bold text-accent-400 uppercase">
                      Current
                    </span>
                  )}
                </div>
                {bw.rosterImpact.length >= 2 && (
                  <AlertIcon className={`h-4 w-4 ${severity.text}`} />
                )}
              </div>

              {/* Teams on bye */}
              <div className="mt-2">
                <p className="text-xs text-surface-500">NFL teams on bye:</p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {bw.teams.map((team) => (
                    <span
                      key={team}
                      className="rounded bg-surface-700/50 px-1.5 py-0.5 text-[11px] font-medium text-surface-300"
                    >
                      {team}
                    </span>
                  ))}
                </div>
              </div>

              {/* Roster impact */}
              {bw.rosterImpact.length > 0 && (
                <div className="mt-2.5 border-t border-surface-700/50 pt-2">
                  <p className={`text-xs font-medium ${severity.text}`}>
                    {bw.rosterImpact.length} starter{bw.rosterImpact.length > 1 ? "s" : ""} affected:
                  </p>
                  <div className="mt-1 space-y-0.5">
                    {bw.rosterImpact.map((player, idx) => (
                      <p key={idx} className="text-xs text-surface-300">
                        {player}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
