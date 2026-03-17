import { useQuery } from "@tanstack/react-query";
import { fetchCurrentPredictions } from "@/lib/api";
import type { WeekPredictionsResponse } from "@/lib/types";

export function useCurrentPredictions() {
  return useQuery<WeekPredictionsResponse>({
    queryKey: ["predictions", "current"],
    queryFn: fetchCurrentPredictions,
  });
}
