import { useTradeSuggestions } from "@/hooks/useTrades";
import { useExplainMode } from "@/context/ExplainModeContext";
import type { TradeSuggestion, Player } from "@/api/client";
import LoadingSpinner from "@/components/shared/LoadingSpinner";
import EmptyState from "@/components/shared/EmptyState";

// ── Arrows icon ────────────────────────────────────────────────────────
function ArrowsIcon({ className }: { className?: string }) {
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
      <polyline points="17 1 21 5 17 9" />
      <path d="M3 11V9a4 4 0 0 1 4-4h14" />
      <polyline points="7 23 3 19 7 15" />
      <path d="M21 13v2a4 4 0 0 1-4 4H3" />
    </svg>
  );
}

// ── Player pill ────────────────────────────────────────────────────────
function PlayerPill({ player }: { player: Player }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-md bg-surface-700/50 px-2 py-1 text-xs font-medium text-surface-200">
      <span className="text-surface-500">{player.position}</span>
      {player.name}
    </span>
  );
}

// ── Fairness gauge ─────────────────────────────────────────────────────
function FairnessGauge({ score }: { score: number }) {
  const clampedScore = Math.max(0, Math.min(100, score));

  let color: string;
  let label: string;
  if (clampedScore >= 70) {
    color = "bg-success-400";
    label = "Great";
  } else if (clampedScore >= 45) {
    color = "bg-accent-400";
    label = "Fair";
  } else {
    color = "bg-danger-400";
    label = "Risky";
  }

  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-surface-700">
        <div
          className={`h-full ${color} transition-all duration-300`}
          style={{ width: `${clampedScore}%` }}
        />
      </div>
      <span className="text-xs text-surface-400">{label}</span>
    </div>
  );
}

// ── Trade suggestion card ──────────────────────────────────────────────
function TradeSuggestionCard({
  suggestion,
}: {
  suggestion: TradeSuggestion;
}) {
  const { explainMode } = useExplainMode();

  return (
    <div className="bg-surface-800 rounded-xl border border-surface-700 p-4 transition-colors hover:border-surface-600">
      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <ArrowsIcon className="h-4 w-4 text-accent-400" />
          <h3 className="text-sm font-semibold text-surface-100">
            Trade with {suggestion.targetTeam.name}
          </h3>
        </div>
        <FairnessGauge score={suggestion.fairnessScore} />
      </div>

      {/* Give / Receive */}
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        {/* You Give */}
        <div className="space-y-1.5">
          <p className="text-xs font-medium text-danger-300">You Give</p>
          <div className="flex flex-wrap gap-1.5">
            {suggestion.sendPlayers.map((p) => (
              <PlayerPill key={p.id} player={p} />
            ))}
          </div>
        </div>

        {/* You Receive */}
        <div className="space-y-1.5">
          <p className="text-xs font-medium text-success-300">You Receive</p>
          <div className="flex flex-wrap gap-1.5">
            {suggestion.receivePlayers.map((p) => (
              <PlayerPill key={p.id} player={p} />
            ))}
          </div>
        </div>
      </div>

      {/* Explanation */}
      {explainMode && suggestion.rationale && (
        <div className="mt-3 rounded-lg bg-primary-800/20 px-3 py-2">
          <p className="text-xs leading-relaxed text-surface-300">
            {suggestion.rationale}
          </p>
        </div>
      )}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────
export default function TradeFinder() {
  const { data: suggestions, isLoading, isError, error, refetch } =
    useTradeSuggestions();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <LoadingSpinner size="lg" label="Finding trade opportunities..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-danger-400/30 bg-danger-400/5 p-6 text-center">
        <p className="text-sm text-danger-300">
          {(error as Error)?.message ?? "Failed to load trade suggestions."}
        </p>
        <button onClick={() => refetch()} className="btn-primary mt-4">
          Retry
        </button>
      </div>
    );
  }

  if (!suggestions || suggestions.length === 0) {
    return (
      <EmptyState
        title="No trade suggestions"
        description="Our AI hasn't found any compelling trade opportunities right now. Check back after roster changes."
      />
    );
  }

  return (
    <div className="space-y-4">
      {suggestions.map((suggestion, idx) => (
        <TradeSuggestionCard key={idx} suggestion={suggestion} />
      ))}
    </div>
  );
}
