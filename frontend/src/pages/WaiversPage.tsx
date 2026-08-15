import WaiverRadar from "@/components/waivers/WaiverRadar";
import { useTrending } from "@/hooks/useWaivers";
import LoadingSpinner from "@/components/shared/LoadingSpinner";

// ── Fire icon ──────────────────────────────────────────────────────────
function FireIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
      stroke="none"
    >
      <path d="M12 23c-3.866 0-7-3.134-7-7 0-2.1.9-4.5 2.3-6.4.3-.4.8-.6 1.2-.4.4.2.6.6.5 1-.3 1.2.1 2.3.8 3 .1-1.8.8-3.5 2-4.8C13.2 7 14.8 5.5 15.5 3c.1-.4.5-.7.9-.7s.8.2.9.6c.7 2 1.7 4.3 1.7 7.1 0 3.866-3.134 7-7 7z" />
    </svg>
  );
}

// ── Trending arrow icons ───────────────────────────────────────────────
function TrendUpIcon({ className }: { className?: string }) {
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
      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
      <polyline points="17 6 23 6 23 12" />
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

// ── Trending sidebar ───────────────────────────────────────────────────
function TrendingSidebar() {
  const { data: trending, isLoading } = useTrending();

  return (
    <div className="bg-surface-800 rounded-xl border border-surface-700 p-4">
      <div className="flex items-center gap-2">
        <FireIcon className="h-5 w-5 text-orange-400" />
        <h2 className="text-sm font-semibold text-surface-100">Trending</h2>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner size="sm" />
        </div>
      )}

      {!isLoading && trending && trending.length > 0 && (
        <div className="mt-3 space-y-2">
          {trending.slice(0, 10).map((tp) => (
            <div
              key={tp.player.id}
              className="flex items-center gap-3 rounded-lg px-2 py-1.5 transition-colors hover:bg-surface-700/50"
            >
              {/* Trend direction */}
              {tp.trend === "up" ? (
                <TrendUpIcon className="h-3.5 w-3.5 flex-shrink-0 text-success-400" />
              ) : (
                <TrendDownIcon className="h-3.5 w-3.5 flex-shrink-0 text-danger-400" />
              )}

              {/* Player info */}
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-medium text-surface-200">
                  {tp.player.name}
                </p>
                <p className="text-[10px] text-surface-500">
                  {tp.player.position} - {tp.player.team}
                </p>
              </div>

              {/* Add/Drop percentages */}
              <div className="flex-shrink-0 text-right">
                <p className="text-[10px] text-success-400">
                  +{tp.addPercentage.toFixed(0)}%
                </p>
                {tp.dropPercentage > 0 && (
                  <p className="text-[10px] text-danger-400">
                    -{tp.dropPercentage.toFixed(0)}%
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {!isLoading && (!trending || trending.length === 0) && (
        <p className="mt-4 text-center text-xs text-surface-500">
          No trending data available.
        </p>
      )}
    </div>
  );
}

// ── Page component ─────────────────────────────────────────────────────
export default function WaiversPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-surface-50">Waivers</h1>
        <p className="mt-1 text-surface-400">
          Discover waiver wire gems and trending pickups
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        {/* Main content */}
        <div>
          <WaiverRadar />
        </div>

        {/* Trending sidebar */}
        <div>
          <TrendingSidebar />
        </div>
      </div>
    </div>
  );
}
