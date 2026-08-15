import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface WeekData {
  week: number;
  yourScore: number;
  opponentScore: number;
}

interface PointsTrendChartProps {
  data: WeekData[];
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ color: string; name: string; value: number }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;

  return (
    <div className="rounded-lg border border-surface-700 bg-surface-800 p-3 shadow-xl">
      <p className="mb-1 text-xs font-medium text-surface-400">
        Week {label}
      </p>
      {payload.map((entry, idx) => (
        <p key={idx} className="text-sm" style={{ color: entry.color }}>
          {entry.name}: {entry.value.toFixed(1)}
        </p>
      ))}
    </div>
  );
}

export default function PointsTrendChart({ data }: PointsTrendChartProps) {
  if (data.length === 0) {
    return (
      <div className="card">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-surface-400">
          Points Trend
        </h2>
        <div className="flex h-48 items-center justify-center">
          <p className="text-sm text-surface-500">No matchup data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-surface-400">
        Points Trend
      </h2>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 4, right: 8, left: -12, bottom: 0 }}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#334155"
              vertical={false}
            />
            <XAxis
              dataKey="week"
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: "#334155" }}
              tickFormatter={(w: number) => `W${w}`}
            />
            <YAxis
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              domain={["dataMin - 10", "dataMax + 10"]}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: 12, color: "#94a3b8" }}
              iconType="circle"
              iconSize={8}
            />
            <Line
              type="monotone"
              dataKey="yourScore"
              name="Your Score"
              stroke="#d69e2e"
              strokeWidth={2.5}
              dot={{ fill: "#d69e2e", strokeWidth: 0, r: 4 }}
              activeDot={{ r: 6, fill: "#d69e2e", stroke: "#1e293b", strokeWidth: 2 }}
            />
            <Line
              type="monotone"
              dataKey="opponentScore"
              name="Opponent"
              stroke="#64748b"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={{ fill: "#64748b", strokeWidth: 0, r: 3 }}
              activeDot={{ r: 5, fill: "#64748b", stroke: "#1e293b", strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
