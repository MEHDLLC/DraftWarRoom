import { useQuery } from "@tanstack/react-query";
import { matchupApi } from "@/api/client";

export function useCurrentMatchup() {
  return useQuery({
    queryKey: ["matchup", "current"],
    queryFn: matchupApi.getCurrent,
    staleTime: 1000 * 60 * 2,
    retry: 2,
  });
}

export function useMatchupByWeek(week: number) {
  return useQuery({
    queryKey: ["matchup", "week", week],
    queryFn: () => matchupApi.getByWeek(week),
    staleTime: 1000 * 60 * 2,
    retry: 2,
  });
}

export function useMatchupAnalysis(week?: number) {
  return useQuery({
    queryKey: ["matchup", "analysis", week],
    queryFn: () => matchupApi.getAnalysis(week),
    staleTime: 1000 * 60 * 2,
    retry: 2,
  });
}
