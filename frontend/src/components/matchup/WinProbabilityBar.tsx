interface WinProbabilityBarProps {
  homeProb: number;
  awayProb: number;
  isUserHome: boolean;
  homeLabel?: string;
  awayLabel?: string;
}

export default function WinProbabilityBar({
  homeProb,
  awayProb,
  isUserHome,
  homeLabel = "Home",
  awayLabel = "Away",
}: WinProbabilityBarProps) {
  const homePercent = Math.round(homeProb * 100);
  const awayPercent = Math.round(awayProb * 100);

  // User's team gets the accent color, opponent is gray
  const homeColor = isUserHome ? "bg-accent-500" : "bg-surface-500";
  const awayColor = isUserHome ? "bg-surface-500" : "bg-accent-500";

  const homeTextColor = isUserHome ? "text-accent-400" : "text-surface-300";
  const awayTextColor = isUserHome ? "text-surface-300" : "text-accent-400";

  return (
    <div className="space-y-2">
      {/* Labels row */}
      <div className="flex items-center justify-between text-xs font-medium">
        <span className={homeTextColor}>{homeLabel}</span>
        <span className="text-surface-500">Win Probability</span>
        <span className={awayTextColor}>{awayLabel}</span>
      </div>

      {/* Bar */}
      <div className="flex h-5 w-full overflow-hidden rounded-full bg-surface-900">
        <div
          className={`${homeColor} flex items-center justify-center transition-all duration-500`}
          style={{ width: `${homePercent}%` }}
        >
          {homePercent >= 15 && (
            <span className="text-[11px] font-bold text-white drop-shadow-sm">
              {homePercent}%
            </span>
          )}
        </div>
        <div
          className={`${awayColor} flex items-center justify-center transition-all duration-500`}
          style={{ width: `${awayPercent}%` }}
        >
          {awayPercent >= 15 && (
            <span className="text-[11px] font-bold text-white drop-shadow-sm">
              {awayPercent}%
            </span>
          )}
        </div>
      </div>

      {/* Percentage labels below (visible when bar is too narrow for inline) */}
      <div className="flex items-center justify-between text-xs">
        <span className={`font-semibold ${homeTextColor}`}>
          {homePercent}%
        </span>
        <span className={`font-semibold ${awayTextColor}`}>
          {awayPercent}%
        </span>
      </div>
    </div>
  );
}
