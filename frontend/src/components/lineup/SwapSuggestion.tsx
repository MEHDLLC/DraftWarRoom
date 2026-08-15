interface SwapPlayer {
  name: string;
  position: string;
  projectedPoints: number;
}

interface SwapSuggestionProps {
  benchPlayer: SwapPlayer;
  starter: SwapPlayer;
  reason: string;
}

export default function SwapSuggestion({
  benchPlayer,
  starter,
  reason,
}: SwapSuggestionProps) {
  const diff = benchPlayer.projectedPoints - starter.projectedPoints;

  return (
    <div className="rounded-xl border border-success-400/30 bg-success-400/5 p-4">
      <div className="mb-2 flex items-center gap-2">
        {/* Swap icon */}
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-success-400/20">
          <svg
            className="h-4 w-4 text-success-400"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="17 1 21 5 17 9" />
            <path d="M3 11V9a4 4 0 014-4h14" />
            <polyline points="7 23 3 19 7 15" />
            <path d="M21 13v2a4 4 0 01-4 4H3" />
          </svg>
        </div>
        <h3 className="text-sm font-semibold text-success-400">
          Suggested Swap
        </h3>
        {diff > 0 && (
          <span className="ml-auto rounded-full bg-success-400/20 px-2 py-0.5 text-xs font-medium text-success-400">
            +{diff.toFixed(1)} pts
          </span>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* Start this player */}
        <div className="flex-1 rounded-lg bg-success-400/10 px-3 py-2">
          <p className="text-[10px] font-medium uppercase text-success-400/70">
            Start
          </p>
          <p className="text-sm font-semibold text-surface-100">
            {benchPlayer.name}
          </p>
          <p className="text-xs text-surface-400">
            {benchPlayer.position} -- {benchPlayer.projectedPoints.toFixed(1)} pts
          </p>
        </div>

        {/* Arrow */}
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-surface-500"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </div>

        {/* Bench this player */}
        <div className="flex-1 rounded-lg bg-surface-700/40 px-3 py-2">
          <p className="text-[10px] font-medium uppercase text-surface-500">
            Bench
          </p>
          <p className="text-sm font-semibold text-surface-300">
            {starter.name}
          </p>
          <p className="text-xs text-surface-500">
            {starter.position} -- {starter.projectedPoints.toFixed(1)} pts
          </p>
        </div>
      </div>

      <p className="mt-2 text-xs text-surface-400">{reason}</p>
    </div>
  );
}
