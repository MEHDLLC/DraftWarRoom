import { type ReactNode } from "react";
import { NavLink } from "react-router-dom";
import Header from "./Header";
import BottomNav from "./BottomNav";

// SVG icon components for the sidebar
function DashboardIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  );
}

function LineupIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
      <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
      <path d="M9 14l2 2 4-4" />
    </svg>
  );
}

function WaiversIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <line x1="19" y1="8" x2="19" y2="14" />
      <line x1="22" y1="11" x2="16" y2="11" />
    </svg>
  );
}

function MatchupIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 9l6 6 6-6" />
      <path d="M6 15l6 6 6-6" />
      <path d="M6 3l6 6 6-6" />
    </svg>
  );
}

function TradesIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="17 1 21 5 17 9" />
      <path d="M3 11V9a4 4 0 0 1 4-4h14" />
      <polyline points="7 23 3 19 7 15" />
      <path d="M21 13v2a4 4 0 0 1-4 4H3" />
    </svg>
  );
}

function ScheduleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  );
}

function DraftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  );
}

function ChatIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}

interface NavItem {
  to: string;
  label: string;
  icon: ({ className }: { className?: string }) => JSX.Element;
}

export const navItems: NavItem[] = [
  { to: "/", label: "Dashboard", icon: DashboardIcon },
  { to: "/lineup", label: "Lineup", icon: LineupIcon },
  { to: "/waivers", label: "Waivers", icon: WaiversIcon },
  { to: "/matchup", label: "Matchup", icon: MatchupIcon },
  { to: "/trades", label: "Trades", icon: TradesIcon },
  { to: "/schedule", label: "Schedule", icon: ScheduleIcon },
  { to: "/draft", label: "Draft", icon: DraftIcon },
  { to: "/chat", label: "Chat", icon: ChatIcon },
];

function SidebarLink({ item }: { item: NavItem }) {
  const Icon = item.icon;

  return (
    <NavLink
      to={item.to}
      end={item.to === "/"}
      className={({ isActive }) =>
        [
          "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150",
          isActive
            ? "bg-primary-800/60 text-accent-400 shadow-sm shadow-primary-900/50"
            : "text-surface-400 hover:bg-surface-800 hover:text-surface-100",
        ].join(" ")
      }
    >
      {({ isActive }) => (
        <>
          <Icon
            className={[
              "h-5 w-5 flex-shrink-0 transition-colors",
              isActive
                ? "text-accent-400"
                : "text-surface-500 group-hover:text-surface-300",
            ].join(" ")}
          />
          <span>{item.label}</span>
        </>
      )}
    </NavLink>
  );
}

export default function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-surface-950">
      {/* Header */}
      <Header />

      <div className="flex flex-1 overflow-hidden">
        {/* Desktop sidebar */}
        <aside className="hidden w-60 flex-shrink-0 border-r border-surface-800 bg-surface-900/50 lg:flex lg:flex-col">
          {/* Logo / Brand */}
          <div className="flex h-14 items-center gap-3 border-b border-surface-800 px-5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-800">
              <span className="text-sm font-bold text-accent-400">DW</span>
            </div>
            <span className="text-base font-bold tracking-tight text-surface-50">
              DraftWarRoom
            </span>
          </div>

          {/* Nav links */}
          <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
            {navItems.map((item) => (
              <SidebarLink key={item.to} item={item} />
            ))}
          </nav>

          {/* Sidebar footer */}
          <div className="border-t border-surface-800 px-4 py-3">
            <p className="text-xs text-surface-500">
              DraftWarRoom v0.1.0
            </p>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>

      {/* Mobile bottom navigation */}
      <BottomNav />
    </div>
  );
}
