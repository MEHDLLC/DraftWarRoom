import { useQuery, useMutation } from "@tanstack/react-query";
import { tradeApi, type TradeAnalysisRequest } from "@/api/client";

export function useAnalyzeTrade() {
  return useMutation({
    mutationFn: (payload: TradeAnalysisRequest) => tradeApi.analyze(payload),
  });
}

export function useTradeSuggestions() {
  return useQuery({
    queryKey: ["trades", "suggestions"],
    queryFn: tradeApi.getSuggestions,
    staleTime: 1000 * 60 * 5,
    retry: 2,
  });
}
