import { useQuery } from "@tanstack/react-query";
import { fetchPredictionHistory } from "@/lib/api";
import type { PredictionHistoryResponse } from "@/lib/types";

export function usePredictionHistory(season?: number, team?: string) {
  return useQuery<PredictionHistoryResponse>({
    queryKey: ["predictions", "history", { season, team }],
    queryFn: () => fetchPredictionHistory(season, team),
  });
}
