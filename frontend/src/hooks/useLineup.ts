import { useQuery } from "@tanstack/react-query";
import { lineupApi } from "@/api/client";

export function useLineupAdvice(week?: number) {
  return useQuery({
    queryKey: ["lineup", "advice", week],
    queryFn: () => lineupApi.getAdvice(week),
    staleTime: 1000 * 60 * 2, // 2 minutes
    retry: 2,
  });
}

export function useOptimalLineup(week?: number) {
  return useQuery({
    queryKey: ["lineup", "optimal", week],
    queryFn: () => lineupApi.getOptimal(week),
    staleTime: 1000 * 60 * 2, // 2 minutes
    retry: 2,
  });
}
