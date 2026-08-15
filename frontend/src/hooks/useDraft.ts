import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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

export function useDraftBoard(autoRefresh = false) {
  return useQuery({
    queryKey: ["draft", "board"],
    queryFn: draftApi.getBoard,
    staleTime: 1000 * 5,
    refetchInterval: autoRefresh ? 1000 * 15 : false, // Poll every 15s during draft
    retry: 2,
  });
}

export function useDraftSuggestions(enabled = true) {
  return useQuery({
    queryKey: ["draft", "suggestions"],
    queryFn: draftApi.getSuggestions,
    staleTime: 1000 * 10,
    enabled,
    retry: 1,
  });
}

export function useDraftRefresh() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: draftApi.refresh,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["draft"] });
    },
  });
}
