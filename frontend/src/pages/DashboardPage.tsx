import { useLeague } from "@/context/LeagueContext";
import { useDashboard } from "@/hooks/useDashboard";
import { useQuery } from "@tanstack/react-query";
import { matchupApi, notificationApi } from "@/api/client";
import RecordCard from "@/components/dashboard/RecordCard";
import AlertsPanel from "@/components/dashboard/AlertsPanel";
import PointsTrendChart from "@/components/dashboard/PointsTrendChart";
import PowerRankingsCard from "@/components/dashboard/PowerRankingsCard";
import LoadingSpinner from "@/components/shared/LoadingSpinner";

export default function DashboardPage() {
  const { league, userTeam, isLoading: leagueLoading } = useLeague();

  const {
    data: dashboard,
    isLoading: dashboardLoading,
    isError: dashboardError,
  } = useDashboard();

  const { data: notifications } = useQuery({
    queryKey: ["notifications"],
    queryFn: notificationApi.getAll,
    staleTime: 1000 * 60 * 2,
    retry: 1,
  });

  // Build points trend data from matchup history
  const currentWeek = league?.week ?? 1;
  const weeks = Array.from({ length: Math.max(0, currentWeek - 1) }, (_, i) => i + 1);

  const matchupQueries = useQuery({
    queryKey: ["matchup-history", currentWeek],
    queryFn: async () => {
      const results = await Promise.allSettled(
        weeks.map((w) => matchupApi.getByWeek(w)),
      );
      return results
        .map((r, idx) => {
          if (r.status === "fulfilled") {
            const m = r.value;
            const isHome = m.homeTeam.id === userTeam?.id;
            const yourScore = isHome
              ? (m.homeTeam.actualScore ?? m.homeTeam.projectedScore)
              : (m.awayTeam.actualScore ?? m.awayTeam.projectedScore);
            const opponentScore = isHome
              ? (m.awayTeam.actualScore ?? m.awayTeam.projectedScore)
              : (m.homeTeam.actualScore ?? m.homeTeam.projectedScore);

            return {
              week: weeks[idx],
              yourScore,
              opponentScore,
            };
          }
          return null;
        })
        .filter(Boolean) as Array<{
        week: number;
        yourScore: number;
        opponentScore: number;
      }>;
    },
    enabled: !!userTeam && weeks.length > 0,
    staleTime: 1000 * 60 * 5,
    retry: 1,
  });

  // Derive recent trend from matchup data
  const recentTrend: Array<"W" | "L"> = (matchupQueries.data ?? [])
    .slice(-5)
    .map((w) => (w.yourScore >= w.opponentScore ? "W" : "L"));

  const isLoading = leagueLoading || dashboardLoading;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-surface-50">Dashboard</h1>
          <p className="mt-1 text-surface-400">
            Your fantasy football command center
          </p>
        </div>
        <div className="flex h-64 items-center justify-center">
          <LoadingSpinner size="lg" label="Loading dashboard..." />
        </div>
      </div>
    );
  }

  if (dashboardError) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-surface-50">Dashboard</h1>
          <p className="mt-1 text-surface-400">
            Your fantasy football command center
          </p>
        </div>
        <div className="card flex flex-col items-center justify-center py-16 text-center">
          <svg
            className="mb-3 h-10 w-10 text-danger-400"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
          <p className="text-sm font-medium text-surface-300">
            Failed to load dashboard data
          </p>
          <p className="mt-1 text-xs text-surface-500">
            Please check your connection and try again
          </p>
        </div>
      </div>
    );
  }

  const record = userTeam?.record ?? { wins: 0, losses: 0, ties: 0 };
  const standing = userTeam?.rank ?? 0;
  const pointsRank = dashboard?.quickStats?.pointsRank
    ? Number(dashboard.quickStats.pointsRank)
    : standing;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-surface-50">Dashboard</h1>
        <p className="mt-1 text-surface-400">
          {league
            ? `${league.name} -- Week ${league.week}`
            : "Your fantasy football command center"}
        </p>
      </div>

      {/* Top Row: Record + Alerts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <RecordCard
          record={record}
          standing={standing}
          pointsRank={pointsRank}
          recentTrend={recentTrend}
        />
        <AlertsPanel alerts={notifications ?? []} />
      </div>

      {/* Points Trend Chart */}
      <PointsTrendChart data={matchupQueries.data ?? []} />

      {/* Power Rankings */}
      <PowerRankingsCard />
    </div>
  );
}
