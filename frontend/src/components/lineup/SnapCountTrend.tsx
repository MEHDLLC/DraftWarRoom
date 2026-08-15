import { AreaChart, Area, ResponsiveContainer, YAxis } from "recharts";

interface SnapCountTrendProps {
  snapCounts: number[];
}

export default function SnapCountTrend({ snapCounts }: SnapCountTrendProps) {
  if (snapCounts.length === 0) {
    return (
      <div className="flex h-8 w-20 items-center justify-center">
        <span className="text-[10px] text-surface-600">No data</span>
      </div>
    );
  }

  const trending =
    snapCounts.length >= 2
      ? snapCounts[snapCounts.length - 1] >= snapCounts[snapCounts.length - 2]
        ? "up"
        : "down"
      : "up";

  const color = trending === "up" ? "#38a169" : "#e53e3e";

  const chartData = snapCounts.map((value, idx) => ({
    week: idx + 1,
    snap: value,
  }));

  return (
    <div className="h-8 w-20">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
          <YAxis
            domain={[0, 100]}
            hide
          />
          <Area
            type="monotone"
            dataKey="snap"
            stroke={color}
            strokeWidth={1.5}
            fill={color}
            fillOpacity={0.15}
            dot={false}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
