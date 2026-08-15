import { useState, useRef, useEffect } from "react";
import { useLeague } from "@/context/LeagueContext";
import { useExplainMode } from "@/context/ExplainModeContext";
import { useNotifications, useUnreadCount, useMarkRead } from "@/hooks/useNotifications";

function BellIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  );
}

function BookOpenIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
    </svg>
  );
}

function SyncIcon({ className, spinning }: { className?: string; spinning?: boolean }) {
  return (
    <svg
      className={[className, spinning ? "animate-spin" : ""].filter(Boolean).join(" ")}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="23 4 23 10 17 10" />
      <polyline points="1 20 1 14 7 14" />
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10" />
      <path d="M20.49 15a9 9 0 0 1-14.85 3.36L1 14" />
    </svg>
  );
}

const priorityColors: Record<string, string> = {
  urgent: "border-l-danger-400",
  high: "border-l-warning-400",
  normal: "border-l-primary-400",
  low: "border-l-surface-600",
};

const typeIcons: Record<string, string> = {
  LINEUP_ALERT: "Starting",
  WAIVER_TIP: "Waiver",
  INJURY: "Injury",
  RECAP: "Recap",
  TRADE_SUGGESTION: "Trade",
};

export default function Header() {
  const { league, isLoading: leagueLoading } = useLeague();
  const { explainMode, toggleExplainMode } = useExplainMode();
  const [syncing, setSyncing] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);

  const { data: unreadData } = useUnreadCount();
  const { data: notifications } = useNotifications();
  const markRead = useMarkRead();

  const unreadCount = unreadData?.unread_count ?? 0;

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setNotifOpen(false);
      }
    }
    if (notifOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [notifOpen]);

  const handleSync = async () => {
    if (syncing) return;
    setSyncing(true);
    try {
      const { leagueApi } = await import("@/api/client");
      await leagueApi.sync();
    } catch {
      // sync error handled elsewhere
    } finally {
      setSyncing(false);
    }
  };

  const handleMarkRead = (id: number) => {
    markRead.mutate(String(id));
  };

  return (
    <header className="flex h-14 flex-shrink-0 items-center justify-between border-b border-surface-800 bg-surface-900/80 px-4 backdrop-blur-sm lg:px-6">
      {/* Left: league info (mobile logo + league name) */}
      <div className="flex items-center gap-3">
        {/* Mobile-only logo */}
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-800 lg:hidden">
          <span className="text-sm font-bold text-accent-400">DW</span>
        </div>

        <div className="flex flex-col">
          {leagueLoading ? (
            <div className="h-5 w-36 animate-pulse rounded bg-surface-700" />
          ) : league ? (
            <>
              <span className="text-sm font-semibold text-surface-100">
                {league.name}
              </span>
              <span className="text-xs text-surface-500">
                Week {league.week} &middot; {league.scoringType}
              </span>
            </>
          ) : (
            <span className="text-sm text-surface-400">
              Connect a league to get started
            </span>
          )}
        </div>
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-2">
        {/* Sync button */}
        <button
          onClick={handleSync}
          disabled={syncing}
          className="btn-ghost p-2"
          title="Sync league data"
          aria-label="Sync league data"
        >
          <SyncIcon className="h-4.5 w-4.5" spinning={syncing} />
        </button>

        {/* Explain mode toggle */}
        <button
          onClick={toggleExplainMode}
          className={[
            "flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors",
            explainMode
              ? "bg-accent-500/20 text-accent-400 ring-1 ring-accent-500/30"
              : "text-surface-400 hover:bg-surface-800 hover:text-surface-200",
          ].join(" ")}
          title={
            explainMode
              ? "Disable beginner-friendly explanations"
              : "Enable beginner-friendly explanations"
          }
          aria-label="Toggle explain mode"
        >
          <BookOpenIcon className="h-4 w-4" />
          <span className="hidden sm:inline">
            {explainMode ? "Explain ON" : "Explain"}
          </span>
        </button>

        {/* Notification bell */}
        <div className="relative" ref={notifRef}>
          <button
            onClick={() => setNotifOpen(!notifOpen)}
            className="btn-ghost relative p-2"
            title="Notifications"
            aria-label="Notifications"
          >
            <BellIcon className="h-5 w-5" />
            {unreadCount > 0 && (
              <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-danger-400 text-[10px] font-bold text-white">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </button>

          {/* Notification dropdown */}
          {notifOpen && (
            <div className="absolute right-0 top-full z-50 mt-1 w-80 max-h-96 overflow-y-auto rounded-xl border border-surface-700 bg-surface-800 shadow-2xl">
              <div className="flex items-center justify-between border-b border-surface-700 px-4 py-3">
                <h3 className="text-sm font-semibold text-surface-100">
                  Notifications
                </h3>
                {unreadCount > 0 && (
                  <span className="rounded-full bg-danger-400/20 px-2 py-0.5 text-xs font-medium text-danger-300">
                    {unreadCount} unread
                  </span>
                )}
              </div>

              {!notifications || notifications.length === 0 ? (
                <div className="px-4 py-8 text-center">
                  <BellIcon className="mx-auto h-8 w-8 text-surface-600" />
                  <p className="mt-2 text-sm text-surface-500">
                    No notifications yet
                  </p>
                  <p className="mt-1 text-xs text-surface-600">
                    You'll see alerts about injuries, waivers, and lineup tips here.
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-surface-700/50">
                  {notifications.map((n) => (
                    <button
                      key={n.id}
                      onClick={() => {
                        if (!n.is_read) handleMarkRead(Number(n.id));
                      }}
                      className={[
                        "w-full border-l-2 px-4 py-3 text-left transition-colors hover:bg-surface-700/30",
                        priorityColors[n.priority] || priorityColors.normal,
                        n.is_read ? "opacity-60" : "",
                      ].join(" ")}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="rounded bg-surface-700 px-1.5 py-0.5 text-[10px] font-medium text-surface-400">
                              {typeIcons[n.type] || n.type}
                            </span>
                            {!n.is_read && (
                              <span className="h-1.5 w-1.5 rounded-full bg-accent-400" />
                            )}
                          </div>
                          <p className="mt-1 text-sm font-medium text-surface-200 truncate">
                            {n.title}
                          </p>
                          <p className="mt-0.5 text-xs text-surface-400 line-clamp-2">
                            {n.body}
                          </p>
                        </div>
                      </div>
                      <p className="mt-1 text-[10px] text-surface-600">
                        {n.created_at}
                      </p>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
