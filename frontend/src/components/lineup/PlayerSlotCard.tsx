import BoomBustMeter from "./BoomBustMeter";

export interface PlayerSlotData {
  id: string;
  name: string;
  position: string;
  team: string;
  slot: string;
  projectedPoints: number;
  compositeScore?: number;
  matchupGrade?: string;
  boomProbability?: number;
  bustProbability?: number;
  status?: string;
  snapCounts?: number[];
}

interface PlayerSlotCardProps {
  player: PlayerSlotData;
}

function getCompositeColor(score: number): string {
  if (score >= 70) return "bg-success-400/20 text-success-400 border-success-400/30";
  if (score >= 40) return "bg-accent-400/20 text-accent-400 border-accent-400/30";
  return "bg-danger-400/20 text-danger-400 border-danger-400/30";
}

function getGradeColor(grade: string): string {
  if (grade.startsWith("A")) return "text-success-400";
  if (grade === "B+" || grade === "B") return "text-primary-300";
  if (grade.startsWith("B") || grade.startsWith("C")) return "text-accent-400";
  return "text-danger-400";
}

function getStatusConfig(status: string): { label: string; color: string } {
  const s = status.toLowerCase();
  if (s === "out") return { label: "OUT", color: "bg-danger-400 text-white" };
  if (s === "doubtful") return { label: "D", color: "bg-danger-400/80 text-white" };
  if (s === "questionable") return { label: "Q", color: "bg-accent-400 text-surface-900" };
  if (s === "probable") return { label: "P", color: "bg-success-400/80 text-white" };
  if (s === "ir") return { label: "IR", color: "bg-danger-400 text-white" };
  if (s === "suspended") return { label: "SUSP", color: "bg-surface-500 text-white" };
  return { label: status.toUpperCase(), color: "bg-surface-500 text-white" };
}

const positionColors: Record<string, string> = {
  QB: "bg-danger-400/20 text-danger-300",
  RB: "bg-success-400/20 text-success-300",
  WR: "bg-primary-300/20 text-primary-200",
  TE: "bg-accent-400/20 text-accent-300",
  K: "bg-surface-400/20 text-surface-300",
  DEF: "bg-surface-400/20 text-surface-300",
  FLEX: "bg-accent-500/20 text-accent-400",
};

export default function PlayerSlotCard({ player }: PlayerSlotCardProps) {
  const posColor = positionColors[player.position] ?? positionColors.FLEX ?? "bg-surface-600/20 text-surface-300";

  return (
    <div className="card flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
      {/* Left: Position badge + Player info */}
      <div className="flex items-center gap-3 sm:min-w-0 sm:flex-1">
        {/* Slot / Position */}
        <div className="flex flex-col items-center gap-1">
          <span className="text-[10px] font-bold uppercase text-surface-500">
            {player.slot}
          </span>
          <span
            className={[
              "rounded-md px-2 py-0.5 text-xs font-bold",
              posColor,
            ].join(" ")}
          >
            {player.position}
          </span>
        </div>

        {/* Name / Team + Status */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate text-sm font-semibold text-surface-100">
              {player.name}
            </p>
            {player.status && player.status !== "active" && player.status !== "Active" && (
              <span
                className={[
                  "flex-shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold leading-none",
                  getStatusConfig(player.status).color,
                ].join(" ")}
              >
                {getStatusConfig(player.status).label}
              </span>
            )}
          </div>
          <p className="text-xs text-surface-500">{player.team}</p>
        </div>
      </div>

      {/* Middle: Scores & Grades */}
      <div className="flex items-center gap-3 sm:gap-4">
        {/* Projected Points */}
        <div className="text-center">
          <p className="text-[10px] text-surface-500">Proj</p>
          <p className="text-lg font-bold tabular-nums text-surface-100">
            {player.projectedPoints.toFixed(1)}
          </p>
        </div>

        {/* Composite Score */}
        {player.compositeScore !== undefined && (
          <div className="text-center">
            <p className="text-[10px] text-surface-500">Score</p>
            <span
              className={[
                "inline-flex items-center justify-center rounded-md border px-2 py-0.5 text-sm font-bold tabular-nums",
                getCompositeColor(player.compositeScore),
              ].join(" ")}
            >
              {player.compositeScore}
            </span>
          </div>
        )}

        {/* Matchup Grade */}
        {player.matchupGrade && (
          <div className="text-center">
            <p className="text-[10px] text-surface-500">Matchup</p>
            <span
              className={[
                "text-lg font-bold",
                getGradeColor(player.matchupGrade),
              ].join(" ")}
            >
              {player.matchupGrade}
            </span>
          </div>
        )}
      </div>

      {/* Right: Boom/Bust */}
      {player.boomProbability !== undefined &&
        player.bustProbability !== undefined && (
          <div className="w-full sm:w-28">
            <BoomBustMeter
              boomProbability={player.boomProbability}
              bustProbability={player.bustProbability}
            />
          </div>
        )}
    </div>
  );
}
