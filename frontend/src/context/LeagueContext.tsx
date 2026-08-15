import {
  createContext,
  useContext,
  type ReactNode,
} from "react";
import { useQuery } from "@tanstack/react-query";
import { leagueApi, type LeagueInfo, type Team } from "@/api/client";

interface LeagueContextValue {
  league: LeagueInfo | undefined;
  teams: Team[] | undefined;
  userTeam: Team | undefined;
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  refetch: () => void;
}

const LeagueContext = createContext<LeagueContextValue | undefined>(undefined);

export function LeagueProvider({ children }: { children: ReactNode }) {
  const leagueQuery = useQuery({
    queryKey: ["league"],
    queryFn: leagueApi.getInfo,
    retry: 1,
  });

  const teamsQuery = useQuery({
    queryKey: ["league", "teams"],
    queryFn: leagueApi.getTeams,
    enabled: !!leagueQuery.data,
    retry: 1,
  });

  const userTeam = teamsQuery.data?.find(
    (t) => t.id === leagueQuery.data?.userTeamId,
  );

  const value: LeagueContextValue = {
    league: leagueQuery.data,
    teams: teamsQuery.data,
    userTeam,
    isLoading: leagueQuery.isLoading || teamsQuery.isLoading,
    isError: leagueQuery.isError || teamsQuery.isError,
    error: leagueQuery.error || teamsQuery.error,
    refetch: () => {
      leagueQuery.refetch();
      teamsQuery.refetch();
    },
  };

  return (
    <LeagueContext.Provider value={value}>{children}</LeagueContext.Provider>
  );
}

export function useLeague(): LeagueContextValue {
  const context = useContext(LeagueContext);
  if (context === undefined) {
    throw new Error("useLeague must be used within a LeagueProvider");
  }
  return context;
}
