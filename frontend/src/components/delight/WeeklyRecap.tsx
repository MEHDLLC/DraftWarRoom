import type { Matchup, RosterPlayer } from "@/api/client";

// ---------------------------------------------------------------------------
// Icons
// ---------------------------------------------------------------------------

function TrophyIcon({ className }: { className?: string }) {
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
      <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" />
      <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18" />
      <path d="M4 22h16" />
      <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20 7 22" />
      <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20 17 22" />
      <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z" />
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
// Trash talk lines
// ---------------------------------------------------------------------------

const WIN_TRASH_TALK = [
  "Another week, another W. Your opponent never stood a chance.",
  "You made that look easy. Time to talk some trash in the group chat.",
  "Dominant performance. Your league mates should be nervous.",
  "Victory tastes sweet. Go ahead and send that screenshot.",
  "That wasn't even close. League domination continues.",
];

const LOSS_TRASH_TALK = [
  "Tough break, but there's always next week. Dust yourself off.",
  "Even the best lose sometimes. Time to hit the waiver wire.",
  "Don't worry -- every champion has a few bad weeks.",
  "Take the L and come back stronger. The season is long.",
  "Not your week, but the comeback arc starts now.",
];

function getTrashTalk(won: boolean): string {
  const lines = won ? WIN_TRASH_TALK : LOSS_TRASH_TALK;
  return lines[Math.floor(Math.random() * lines.length)];
}

// ---------------------------------------------------------------------------
// WeeklyRecap
// ---------------------------------------------------------------------------

interface WeeklyRecapProps {
  matchup: Matchup;
  roster?: RosterPlayer[];
  userTeamId: string;
}

export default function WeeklyRecap({
  matchup,
  roster,
  userTeamId,
}: WeeklyRecapProps) {
  // Determine which side is the user
  const isHome = matchup.homeTeam.id === userTeamId;
  const userTeam = isHome ? matchup.homeTeam : matchup.awayTeam;
  const opponentTeam = isHome ? matchup.awayTeam : matchup.homeTeam;

  const userScore = userTeam.actualScore ?? userTeam.projectedScore;
  const opponentScore =
    opponentTeam.actualScore ?? opponentTeam.projectedScore;
  const won = userScore > opponentScore;

  // Find MVP and Bust from roster if available
  const starters = roster?.filter((p) => p.slot !== "BN" && p.slot !== "IR");
  const mvp = starters?.reduce<RosterPlayer | null>((best, player) => {
    if (!best || player.projectedPoints > best.projectedPoints) return player;
    return best;
  }, null);

  // Bust: the player who scored furthest below projection (using 0 as actual since we
  // don't have individual actuals in the type -- this is a visual stub)
  const bust = starters?.reduce<RosterPlayer | null>((worst, player) => {
    if (!worst || player.projectedPoints < worst.projectedPoints) return player;
    return worst;
  }, null);

  return (
    <div
      className={[
        "card overflow-hidden",
        won ? "border-success-400/30" : "border-danger-400/30",
      ].join(" ")}
    >
      {/* Accent top border */}
      <div
        className={[
          "h-1 w-full",
          won ? "bg-success-400" : "bg-danger-400",
        ].join(" ")}
      />

      <div className="p-5">
        {/* Header */}
        <div className="mb-4 flex items-center gap-3">
          <div
            className={[
              "flex h-10 w-10 items-center justify-center rounded-xl",
              won ? "bg-success-400/15" : "bg-danger-400/15",
            ].join(" ")}
          >
            {won ? (
              <TrophyIcon className="h-5 w-5 text-success-400" />
            ) : (
              <TrendDownIcon className="h-5 w-5 text-danger-400" />
            )}
          </div>
          <div>
            <h3 className="text-base font-semibold text-surface-100">
              Week {matchup.week} Recap
            </h3>
            <p
              className={[
                "text-sm font-medium",
                won ? "text-success-400" : "text-danger-400",
              ].join(" ")}
            >
              {won ? "Victory!" : "Defeat"}
            </p>
          </div>
        </div>

        {/* Score comparison */}
        <div className="mb-5 flex items-center justify-between rounded-xl bg-surface-900/60 p-4">
          <div className="text-center">
            <p className="text-xs font-medium text-surface-400">
              {userTeam.name}
            </p>
            <p
              className={[
                "mt-1 text-2xl font-bold",
                won ? "text-success-400" : "text-danger-400",
              ].join(" ")}
            >
              {userScore.toFixed(1)}
            </p>
          </div>
          <span className="text-sm font-medium text-surface-500">vs</span>
          <div className="text-center">
            <p className="text-xs font-medium text-surface-400">
              {opponentTeam.name}
            </p>
            <p className="mt-1 text-2xl font-bold text-surface-200">
              {opponentScore.toFixed(1)}
            </p>
          </div>
        </div>

        {/* MVP and Bust */}
        {starters && starters.length > 0 && (
          <div className="mb-5 grid grid-cols-2 gap-3">
            {/* MVP */}
            {mvp && (
              <div className="rounded-lg border border-success-400/20 bg-success-400/5 p-3">
                <p className="text-xs font-medium text-success-400">
                  MVP of the Week
                </p>
                <p className="mt-1 text-sm font-semibold text-surface-100">
                  {mvp.name}
                </p>
                <p className="text-xs text-surface-400">
                  {mvp.projectedPoints.toFixed(1)} pts &middot; {mvp.position}
                </p>
              </div>
            )}

            {/* Bust */}
            {bust && bust.id !== mvp?.id && (
              <div className="rounded-lg border border-danger-400/20 bg-danger-400/5 p-3">
                <p className="text-xs font-medium text-danger-400">
                  Bust of the Week
                </p>
                <p className="mt-1 text-sm font-semibold text-surface-100">
                  {bust.name}
                </p>
                <p className="text-xs text-surface-400">
                  {bust.projectedPoints.toFixed(1)} pts &middot;{" "}
                  {bust.position}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Trash talk */}
        <div className="rounded-lg bg-surface-800/60 px-4 py-3">
          <p className="text-sm italic text-surface-300">
            &ldquo;{getTrashTalk(won)}&rdquo;
          </p>
        </div>
      </div>
    </div>
  );
}
