import { useQuery } from "@tanstack/react-query";
import { fetchModelInfo } from "@/lib/api";
import type { ModelInfoResponse } from "@/lib/types";

export function useModelInfo() {
  return useQuery<ModelInfoResponse>({
    queryKey: ["model", "info"],
    queryFn: fetchModelInfo,
  });
}
