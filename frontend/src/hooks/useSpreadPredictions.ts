import { useQuery } from "@tanstack/react-query";
import { fetchSpreadPredictions } from "@/lib/api";
import type { SpreadWeekResponse } from "@/lib/types";

export function useSpreadPredictions(season?: number, week?: number) {
  return useQuery<SpreadWeekResponse>({
    queryKey: ["predictions", "spreads", { season, week }],
    queryFn: () => fetchSpreadPredictions(season!, week!),
    enabled: season != null && week != null,
  });
}
