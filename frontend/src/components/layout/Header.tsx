import { useState } from "react";
import { useLeague } from "@/context/LeagueContext";
import { useExplainMode } from "@/context/ExplainModeContext";

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

export default function Header() {
  const { league, isLoading: leagueLoading } = useLeague();
  const { explainMode, toggleExplainMode } = useExplainMode();
  const [syncing, setSyncing] = useState(false);

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
        <button
          className="btn-ghost relative p-2"
          title="Notifications"
          aria-label="Notifications"
        >
          <BellIcon className="h-5 w-5" />
          {/* Unread indicator dot */}
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-danger-400" />
        </button>
      </div>
    </header>
  );
}
