import type { AppNotification } from "@/api/client";

interface AlertsPanelProps {
  alerts: AppNotification[];
}

const typeConfig: Record<
  string,
  { color: string; bgColor: string; icon: string }
> = {
  INJURY: {
    color: "text-danger-400",
    bgColor: "bg-danger-400/10 border-danger-400/30",
    icon: "M12 9v2m0 4h.01M5.07 19h13.86c1.54 0 2.5-1.67 1.73-3L13.73 4c-.77-1.33-2.69-1.33-3.46 0L3.34 16c-.77 1.33.19 3 1.73 3z",
  },
  WAIVER_TIP: {
    color: "text-success-400",
    bgColor: "bg-success-400/10 border-success-400/30",
    icon: "M12 4v16m8-8H4",
  },
  LINEUP_ALERT: {
    color: "text-accent-400",
    bgColor: "bg-accent-400/10 border-accent-400/30",
    icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2",
  },
  TRADE_SUGGESTION: {
    color: "text-primary-300",
    bgColor: "bg-primary-400/10 border-primary-400/30",
    icon: "M8 7h12m-12 6h12m-12 6h12M4 7h.01M4 13h.01M4 19h.01",
  },
  RECAP: {
    color: "text-surface-400",
    bgColor: "bg-surface-400/10 border-surface-400/30",
    icon: "M13 16h-1v-4h-1m1-4h.01M12 2a10 10 0 100 20 10 10 0 000-20z",
  },
};

const defaultConfig = {
  color: "text-surface-400",
  bgColor: "bg-surface-400/10 border-surface-400/30",
  icon: "M13 16h-1v-4h-1m1-4h.01M12 2a10 10 0 100 20 10 10 0 000-20z",
};

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export default function AlertsPanel({ alerts }: AlertsPanelProps) {
  if (alerts.length === 0) {
    return (
      <div className="card">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-surface-400">
          Alerts
        </h2>
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <svg
            className="mb-2 h-8 w-8 text-surface-600"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 01-3.46 0" />
          </svg>
          <p className="text-sm text-surface-500">No new alerts</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-surface-400">
          Alerts
        </h2>
        <span className="rounded-full bg-danger-400/20 px-2 py-0.5 text-xs font-medium text-danger-400">
          {alerts.filter((a) => !a.is_read).length} new
        </span>
      </div>

      <div className="space-y-2">
        {alerts.map((alert) => {
          const config = typeConfig[alert.type] || defaultConfig;

          return (
            <div
              key={alert.id}
              className={[
                "flex gap-3 rounded-lg border p-3 transition-colors",
                config.bgColor,
                alert.is_read ? "opacity-60" : "",
              ].join(" ")}
            >
              <div className="flex-shrink-0 pt-0.5">
                <svg
                  className={["h-4 w-4", config.color].join(" ")}
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d={config.icon} />
                </svg>
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-surface-100">
                  {alert.title}
                </p>
                <p className="mt-0.5 text-xs text-surface-400">
                  {alert.body}
                </p>
                <p className="mt-1 text-xs text-surface-600">
                  {formatTimestamp(alert.created_at)}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
