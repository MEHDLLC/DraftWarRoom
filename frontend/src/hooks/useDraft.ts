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
    refetchInterval: autoRefresh ? 1000 * 15 : false,
    retry: 2,
  });
}

export function useDraftSuggestions(enabled = true) {
  return useQuery({
    queryKey: ["draft", "suggestions"],
    queryFn: draftApi.getSuggestions,
    staleTime: 1000 * 5,
    enabled,
    retry: 1,
  });
}

export function useLiveDraftState() {
  return useQuery({
    queryKey: ["draft", "live-state"],
    queryFn: draftApi.getLiveState,
    staleTime: 1000 * 2,
    retry: 1,
  });
}

export function useAvailablePlayers(q = "", position = "") {
  return useQuery({
    queryKey: ["draft", "available", q, position],
    queryFn: () => draftApi.getAvailable({ q: q || undefined, position: position || undefined, limit: 100 }),
    staleTime: 1000 * 3,
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

export function useMarkPicked() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (playerId: number) => draftApi.markPicked(playerId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["draft"] });
    },
  });
}

export function useUndoLastPick() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: draftApi.undoLast,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["draft"] });
    },
  });
}

export function useRemovePick() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (overallPick: number) => draftApi.removePick(overallPick),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["draft"] });
    },
  });
}

export function useSetMyPosition() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (position: number) => draftApi.setMyPosition(position),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["draft"] });
    },
  });
}

export function useSetDraftOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (order: { team_id: number; position: number }[]) =>
      draftApi.setDraftOrder(order),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["draft"] });
    },
  });
}
