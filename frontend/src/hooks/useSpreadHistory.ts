import { useQuery } from "@tanstack/react-query";
import { fetchSpreadHistory } from "@/lib/api";
import type { SpreadHistoryResponse } from "@/lib/types";

export function useSpreadHistory(season?: number, enabled: boolean = true) {
  return useQuery<SpreadHistoryResponse>({
    queryKey: ["predictions", "spreads", "history", { season }],
    queryFn: () => fetchSpreadHistory(season),
    enabled,
    retry: 2,
  });
}
