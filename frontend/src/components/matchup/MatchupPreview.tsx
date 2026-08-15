import type { Matchup } from "@/api/client";
import WinProbabilityBar from "./WinProbabilityBar";
import { useLeague } from "@/context/LeagueContext";

// ── Advantage indicator ────────────────────────────────────────────────
function AdvantageChip({
  label,
  side,
}: {
  label: string;
  side: "home" | "away";
}) {
  const color =
    side === "home"
      ? "bg-success-400/10 text-success-400 border-success-400/20"
      : "bg-danger-400/10 text-danger-400 border-danger-400/20";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium ${color}`}
    >
      {label}
    </span>
  );
}

// ── Team column ────────────────────────────────────────────────────────
function TeamColumn({
  name,
  projectedScore,
  actualScore,
  isUser,
}: {
  name: string;
  projectedScore: number;
  actualScore?: number;
  isUser: boolean;
}) {
  return (
    <div className="flex flex-1 flex-col items-center gap-2 text-center">
      <div
        className={[
          "flex h-14 w-14 items-center justify-center rounded-full border-2",
          isUser
            ? "border-accent-400 bg-accent-400/10"
            : "border-surface-600 bg-surface-700",
        ].join(" ")}
      >
        <span className="text-lg font-bold text-surface-100">
          {name.charAt(0).toUpperCase()}
        </span>
      </div>

      <h3
        className={[
          "text-sm font-semibold",
          isUser ? "text-accent-400" : "text-surface-100",
        ].join(" ")}
      >
        {name}
      </h3>

      <div className="space-y-0.5">
        {actualScore !== undefined && (
          <p className="text-2xl font-bold text-surface-50">
            {actualScore.toFixed(1)}
          </p>
        )}
        <p
          className={[
            "text-xs",
            actualScore !== undefined
              ? "text-surface-500"
              : "text-lg font-bold text-surface-200",
          ].join(" ")}
        >
          {actualScore !== undefined ? "Proj: " : ""}
          {projectedScore.toFixed(1)}
          {actualScore === undefined && (
            <span className="ml-1 text-xs font-normal text-surface-500">
              proj
            </span>
          )}
        </p>
      </div>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────
interface MatchupPreviewProps {
  matchup: Matchup;
  className?: string;
}

export default function MatchupPreview({
  matchup,
  className = "",
}: MatchupPreviewProps) {
  const { league } = useLeague();
  const userTeamId = league?.userTeamId;

  const isUserHome = matchup.homeTeam.id === userTeamId;
  const isUserAway = matchup.awayTeam.id === userTeamId;

  // Win probability from the API is for the home team
  const homeProb = matchup.winProbability;
  const awayProb = 1 - matchup.winProbability;

  // Determine advantages
  const projDiff =
    matchup.homeTeam.projectedScore - matchup.awayTeam.projectedScore;
  const advantages: { label: string; side: "home" | "away" }[] = [];

  if (Math.abs(projDiff) > 5) {
    advantages.push({
      label: `${Math.abs(projDiff).toFixed(1)} pt edge`,
      side: projDiff > 0 ? "home" : "away",
    });
  }
  if (Math.abs(homeProb - awayProb) > 0.2) {
    advantages.push({
      label: "Favored",
      side: homeProb > awayProb ? "home" : "away",
    });
  }

  return (
    <div
      className={[
        "bg-surface-800 rounded-xl border border-surface-700 p-5",
        className,
      ].join(" ")}
    >
      {/* Week label */}
      <div className="mb-4 text-center">
        <span className="rounded-md bg-surface-900 px-3 py-1 text-xs font-medium text-surface-400">
          Week {matchup.week}
        </span>
      </div>

      {/* ── Head-to-head ── */}
      <div className="flex items-center gap-4">
        <TeamColumn
          name={matchup.homeTeam.name}
          projectedScore={matchup.homeTeam.projectedScore}
          actualScore={matchup.homeTeam.actualScore}
          isUser={isUserHome}
        />

        <div className="flex flex-col items-center gap-1">
          <span className="text-xs font-bold text-surface-500 uppercase tracking-widest">
            VS
          </span>
        </div>

        <TeamColumn
          name={matchup.awayTeam.name}
          projectedScore={matchup.awayTeam.projectedScore}
          actualScore={matchup.awayTeam.actualScore}
          isUser={isUserAway}
        />
      </div>

      {/* ── Win Probability ── */}
      <div className="mt-5">
        <WinProbabilityBar
          homeProb={homeProb}
          awayProb={awayProb}
          isUserHome={isUserHome || (!isUserAway && true)}
          homeLabel={matchup.homeTeam.name}
          awayLabel={matchup.awayTeam.name}
        />
      </div>

      {/* ── Key Matchup Advantages ── */}
      {advantages.length > 0 && (
        <div className="mt-4 space-y-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-surface-500">
            Key Advantages
          </h4>
          <div className="flex flex-wrap gap-2">
            {advantages.map((adv, i) => (
              <AdvantageChip key={i} label={adv.label} side={adv.side} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
