import { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";
import { LeagueProvider } from "@/context/LeagueContext";
import { ExplainModeProvider } from "@/context/ExplainModeContext";
import AppShell from "@/components/layout/AppShell";
import LoadingSpinner from "@/components/shared/LoadingSpinner";
import ErrorBoundary from "@/components/shared/ErrorBoundary";

const DashboardPage = lazy(() => import("@/pages/DashboardPage"));
const LineupPage = lazy(() => import("@/pages/LineupPage"));
const WaiversPage = lazy(() => import("@/pages/WaiversPage"));
const MatchupPage = lazy(() => import("@/pages/MatchupPage"));
const TradesPage = lazy(() => import("@/pages/TradesPage"));
const SchedulePage = lazy(() => import("@/pages/SchedulePage"));
const DraftPage = lazy(() => import("@/pages/DraftPage"));
const ChatPage = lazy(() => import("@/pages/ChatPage"));

function PageFallback() {
  return (
    <div className="flex h-64 items-center justify-center">
      <LoadingSpinner size="lg" />
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <ExplainModeProvider>
        <LeagueProvider>
          <AppShell>
            <Suspense fallback={<PageFallback />}>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/lineup" element={<LineupPage />} />
                <Route path="/waivers" element={<WaiversPage />} />
                <Route path="/matchup" element={<MatchupPage />} />
                <Route path="/trades" element={<TradesPage />} />
                <Route path="/schedule" element={<SchedulePage />} />
                <Route path="/draft" element={<DraftPage />} />
                <Route path="/chat" element={<ChatPage />} />
              </Routes>
            </Suspense>
          </AppShell>
        </LeagueProvider>
      </ExplainModeProvider>
    </ErrorBoundary>
  );
}
