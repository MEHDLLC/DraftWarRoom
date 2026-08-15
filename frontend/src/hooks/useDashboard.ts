import { useQuery } from "@tanstack/react-query";
import { leagueApi } from "@/api/client";

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: leagueApi.getDashboard,
    staleTime: 1000 * 60 * 2, // 2 minutes
    retry: 2,
  });
}

export function usePowerRankings() {
  return useQuery({
    queryKey: ["power-rankings"],
    queryFn: leagueApi.getPowerRankings,
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: 2,
  });
}
