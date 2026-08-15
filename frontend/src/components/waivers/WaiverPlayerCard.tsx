import type { WaiverRecommendation } from "@/api/client";
import { useExplainMode } from "@/context/ExplainModeContext";

// ── Position badge colors ──────────────────────────────────────────────
const positionColors: Record<string, string> = {
  QB: "bg-pink-500/20 text-pink-300",
  RB: "bg-emerald-500/20 text-emerald-300",
  WR: "bg-sky-500/20 text-sky-300",
  TE: "bg-orange-500/20 text-orange-300",
  K: "bg-purple-500/20 text-purple-300",
  DEF: "bg-yellow-500/20 text-yellow-300",
};

// ── Composite score ring color ─────────────────────────────────────────
function scoreColor(score: number): string {
  if (score >= 80) return "text-success-400 border-success-400";
  if (score >= 60) return "text-accent-400 border-accent-400";
  if (score >= 40) return "text-orange-400 border-orange-400";
  return "text-danger-400 border-danger-400";
}

// ── Boom/Bust meter ────────────────────────────────────────────────────
function BoomBustMeter({ score }: { score: number }) {
  const clampedScore = Math.max(0, Math.min(100, score));
  const boomWidth = clampedScore;
  const bustWidth = 100 - clampedScore;

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-surface-400">
        <span>Bust</span>
        <span>Boom</span>
      </div>
      <div className="flex h-2 w-full overflow-hidden rounded-full bg-surface-700">
        <div
          className="bg-danger-400/60 transition-all duration-300"
          style={{ width: `${bustWidth}%` }}
        />
        <div
          className="bg-success-400 transition-all duration-300"
          style={{ width: `${boomWidth}%` }}
        />
      </div>
    </div>
  );
}

// ── Fire trending icon ─────────────────────────────────────────────────
function FireIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
      stroke="none"
    >
      <path d="M12 23c-3.866 0-7-3.134-7-7 0-2.1.9-4.5 2.3-6.4.3-.4.8-.6 1.2-.4.4.2.6.6.5 1-.3 1.2.1 2.3.8 3 .1-1.8.8-3.5 2-4.8C13.2 7 14.8 5.5 15.5 3c.1-.4.5-.7.9-.7s.8.2.9.6c.7 2 1.7 4.3 1.7 7.1 0 3.866-3.134 7-7 7z" />
    </svg>
  );
}

// ── Arrow icons ────────────────────────────────────────────────────────
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
      <path d="M12 5v14M19 12l-7 7-7-7" />
    </svg>
  );
}

// ── Main component ─────────────────────────────────────────────────────
interface WaiverPlayerCardProps {
  recommendation: WaiverRecommendation;
  className?: string;
}

export default function WaiverPlayerCard({
  recommendation,
  className = "",
}: WaiverPlayerCardProps) {
  const { explainMode } = useExplainMode();
  const { player, priority, dropCandidate, reason, faabSuggestion } =
    recommendation;

  const posClass = positionColors[player.position] ?? "bg-surface-600/20 text-surface-300";

  return (
    <div
      className={[
        "bg-surface-800 rounded-xl border border-surface-700 p-4 transition-colors hover:border-surface-600",
        className,
      ].join(" ")}
    >
      {/* ── Header: Player info + composite score ── */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className={`inline-flex rounded px-1.5 py-0.5 text-xs font-bold ${posClass}`}>
              {player.position}
            </span>
            <h3 className="truncate text-sm font-semibold text-surface-50">
              {player.name}
            </h3>
          </div>
          <p className="mt-0.5 text-xs text-surface-400">{player.team}</p>
        </div>

        {/* Composite Score Badge */}
        <div
          className={`flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-full border-2 ${scoreColor(
            player.projectedPoints
          )}`}
        >
          <span className="text-sm font-bold">{priority}</span>
        </div>
      </div>

      {/* ── Trending indicator ── */}
      {player.averagePoints > 0 && (
        <div className="mt-3 flex items-center gap-1.5">
          <FireIcon className="h-4 w-4 text-orange-400" />
          <span className="text-xs font-medium text-orange-300">
            Trending #{Math.round(player.averagePoints)}
          </span>
        </div>
      )}

      {/* ── Boom/Bust Meter ── */}
      <div className="mt-3">
        <BoomBustMeter score={player.projectedPoints} />
      </div>

      {/* ── Stats row ── */}
      <div className="mt-3 flex items-center gap-4 text-xs text-surface-400">
        <span>
          Proj: <span className="font-medium text-surface-200">{player.projectedPoints.toFixed(1)}</span>
        </span>
        <span>
          Avg: <span className="font-medium text-surface-200">{player.averagePoints.toFixed(1)}</span>
        </span>
        {faabSuggestion !== undefined && (
          <span>
            FAAB: <span className="font-medium text-accent-400">${faabSuggestion}</span>
          </span>
        )}
      </div>

      {/* ── Suggested Drop ── */}
      {dropCandidate && (
        <div className="mt-3 rounded-lg border border-danger-400/20 bg-danger-400/5 px-3 py-2">
          <div className="flex items-center gap-2">
            <ArrowDownIcon className="h-3.5 w-3.5 text-danger-400" />
            <span className="text-xs font-medium text-danger-300">
              Suggested Drop
            </span>
          </div>
          <p className="mt-1 text-xs text-surface-300">
            {dropCandidate.name}{" "}
            <span className="text-surface-500">
              ({dropCandidate.position} - {dropCandidate.team})
            </span>
          </p>
        </div>
      )}

      {/* ── Explanation ── */}
      {explainMode && reason && (
        <div className="mt-3 rounded-lg bg-primary-800/20 px-3 py-2">
          <p className="text-xs leading-relaxed text-surface-300">{reason}</p>
        </div>
      )}
    </div>
  );
}
