import { useQuery } from "@tanstack/react-query";
import { fetchExperiments } from "@/lib/api";
import type { ExperimentResponse } from "@/lib/types";

export function useExperiments() {
  return useQuery<ExperimentResponse[]>({
    queryKey: ["experiments"],
    queryFn: fetchExperiments,
  });
}
