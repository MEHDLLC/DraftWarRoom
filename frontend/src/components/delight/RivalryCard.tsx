// ---------------------------------------------------------------------------
// Icons
// ---------------------------------------------------------------------------

function SwordsIcon({ className }: { className?: string }) {
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
      <polyline points="14.5 17.5 3 6 3 3 6 3 17.5 14.5" />
      <line x1="13" y1="19" x2="19" y2="13" />
      <line x1="16" y1="16" x2="20" y2="20" />
      <line x1="19" y1="21" x2="21" y2="19" />
      <polyline points="14.5 6.5 18 3 21 3 21 6 17.5 9.5" />
      <line x1="5" y1="14" x2="9" y2="18" />
      <line x1="7" y1="17" x2="4" y2="20" />
      <line x1="3" y1="19" x2="5" y2="21" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface MatchupHistoryEntry {
  week: number;
  season: number;
  userScore: number;
  opponentScore: number;
}

interface RivalryCardProps {
  opponentTeam: {
    id: string;
    name: string;
    owner: string;
  };
  matchupHistory: MatchupHistoryEntry[];
}

// ---------------------------------------------------------------------------
// RivalryCard
// ---------------------------------------------------------------------------

export default function RivalryCard({
  opponentTeam,
  matchupHistory,
}: RivalryCardProps) {
  // Calculate stats
  const wins = matchupHistory.filter(
    (m) => m.userScore > m.opponentScore,
  ).length;
  const losses = matchupHistory.filter(
    (m) => m.userScore < m.opponentScore,
  ).length;
  const ties = matchupHistory.length - wins - losses;

  const avgScore =
    matchupHistory.length > 0
      ? matchupHistory.reduce((sum, m) => sum + m.userScore, 0) /
        matchupHistory.length
      : 0;

  const avgOpponentScore =
    matchupHistory.length > 0
      ? matchupHistory.reduce((sum, m) => sum + m.opponentScore, 0) /
        matchupHistory.length
      : 0;

  // Find biggest win and biggest loss
  let biggestWin: MatchupHistoryEntry | null = null;
  let biggestLoss: MatchupHistoryEntry | null = null;

  for (const m of matchupHistory) {
    const diff = m.userScore - m.opponentScore;
    if (diff > 0 && (!biggestWin || diff > biggestWin.userScore - biggestWin.opponentScore)) {
      biggestWin = m;
    }
    if (diff < 0 && (!biggestLoss || diff < biggestLoss.userScore - biggestLoss.opponentScore)) {
      biggestLoss = m;
    }
  }

  const isWinning = wins > losses;
  const isTied = wins === losses;

  return (
    <div className="card overflow-hidden">
      {/* Accent top bar */}
      <div className="h-1 w-full bg-gradient-to-r from-primary-800 via-accent-500 to-primary-800" />

      <div className="p-5">
        {/* Header */}
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-800/50">
            <SwordsIcon className="h-5 w-5 text-accent-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-base font-semibold text-surface-100">
              vs {opponentTeam.name}
            </h3>
            <p className="text-xs text-surface-400">
              {opponentTeam.owner} &middot; {matchupHistory.length} meetings
            </p>
          </div>
        </div>

        {/* All-time record */}
        <div className="mb-4 flex items-center justify-center gap-4 rounded-xl bg-surface-900/60 py-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-success-400">{wins}</p>
            <p className="text-xs text-surface-400">Wins</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-surface-400">{ties}</p>
            <p className="text-xs text-surface-400">Ties</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-danger-400">{losses}</p>
            <p className="text-xs text-surface-400">Losses</p>
          </div>
        </div>

        {/* Rivalry status */}
        <div className="mb-4 text-center">
          <span
            className={[
              "inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold",
              isWinning
                ? "bg-success-400/15 text-success-400"
                : isTied
                  ? "bg-accent-500/15 text-accent-400"
                  : "bg-danger-400/15 text-danger-400",
            ].join(" ")}
          >
            {isWinning
              ? "You own this rivalry"
              : isTied
                ? "Dead even"
                : "They have the edge"}
          </span>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-3">
          {/* Your avg score */}
          <div className="rounded-lg border border-surface-700/40 bg-surface-800/50 p-3 text-center">
            <p className="text-xs text-surface-400">Your Avg Score</p>
            <p className="mt-0.5 text-lg font-bold text-surface-100">
              {avgScore.toFixed(1)}
            </p>
          </div>

          {/* Their avg score */}
          <div className="rounded-lg border border-surface-700/40 bg-surface-800/50 p-3 text-center">
            <p className="text-xs text-surface-400">Their Avg Score</p>
            <p className="mt-0.5 text-lg font-bold text-surface-100">
              {avgOpponentScore.toFixed(1)}
            </p>
          </div>

          {/* Biggest win */}
          <div className="rounded-lg border border-success-400/20 bg-success-400/5 p-3 text-center">
            <p className="text-xs text-success-400">Biggest Win</p>
            {biggestWin ? (
              <p className="mt-0.5 text-lg font-bold text-success-400">
                +
                {(biggestWin.userScore - biggestWin.opponentScore).toFixed(1)}
              </p>
            ) : (
              <p className="mt-0.5 text-sm text-surface-500">N/A</p>
            )}
          </div>

          {/* Biggest loss */}
          <div className="rounded-lg border border-danger-400/20 bg-danger-400/5 p-3 text-center">
            <p className="text-xs text-danger-400">Biggest Loss</p>
            {biggestLoss ? (
              <p className="mt-0.5 text-lg font-bold text-danger-400">
                {(biggestLoss.userScore - biggestLoss.opponentScore).toFixed(1)}
              </p>
            ) : (
              <p className="mt-0.5 text-sm text-surface-500">N/A</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
