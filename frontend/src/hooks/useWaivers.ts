import { useQuery } from "@tanstack/react-query";
import { waiverApi } from "@/api/client";

export function useWaiverRecommendations(position?: string, limit?: number) {
  return useQuery({
    queryKey: ["waivers", "recommendations", position, limit],
    queryFn: () => waiverApi.getRecommendations({ position, limit }),
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: 2,
  });
}

export function useTrending(period?: string) {
  return useQuery({
    queryKey: ["waivers", "trending", period],
    queryFn: () => waiverApi.getTrending({ period }),
    staleTime: 1000 * 60 * 5,
    retry: 2,
  });
}
