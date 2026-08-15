import { useQuery } from "@tanstack/react-query";
import { draftApi } from "@/api/client";

export function useDraftPicks() {
  return useQuery({
    queryKey: ["draft", "picks"],
    queryFn: draftApi.getPicks,
    staleTime: 1000 * 60 * 5,
    retry: 2,
  });
}

export function useDraftValueTracker() {
  return useQuery({
    queryKey: ["draft", "value-tracker"],
    queryFn: draftApi.getValueTracker,
    staleTime: 1000 * 60 * 5,
    retry: 2,
  });
}
