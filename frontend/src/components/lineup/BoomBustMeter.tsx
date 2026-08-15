interface BoomBustMeterProps {
  boomProbability: number;
  bustProbability: number;
}

export default function BoomBustMeter({
  boomProbability,
  bustProbability,
}: BoomBustMeterProps) {
  const middleProbability = Math.max(
    0,
    100 - boomProbability - bustProbability,
  );

  return (
    <div className="w-full">
      <div className="flex h-2 w-full overflow-hidden rounded-full bg-surface-700">
        {/* Boom (green) */}
        {boomProbability > 0 && (
          <div
            className="bg-success-400 transition-all duration-300"
            style={{ width: `${boomProbability}%` }}
            title={`Boom: ${boomProbability}%`}
          />
        )}

        {/* Middle (gray) */}
        {middleProbability > 0 && (
          <div
            className="bg-surface-500 transition-all duration-300"
            style={{ width: `${middleProbability}%` }}
            title={`Average: ${middleProbability}%`}
          />
        )}

        {/* Bust (red) */}
        {bustProbability > 0 && (
          <div
            className="bg-danger-400 transition-all duration-300"
            style={{ width: `${bustProbability}%` }}
            title={`Bust: ${bustProbability}%`}
          />
        )}
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-surface-500">
        <span className="text-success-400/70">{boomProbability}% boom</span>
        <span className="text-danger-400/70">{bustProbability}% bust</span>
      </div>
    </div>
  );
}
