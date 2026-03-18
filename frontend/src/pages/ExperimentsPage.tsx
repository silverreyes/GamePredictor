import { useEffect } from "react";
import { useExperiments } from "@/hooks/useExperiments";
import { ExperimentTable } from "@/components/experiments/ExperimentTable";
import { ErrorState } from "@/components/shared/ErrorState";
import { ApiError } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

export function ExperimentsPage() {
  const { data, isLoading, isError, error, refetch } = useExperiments();

  useEffect(() => {
    document.title = "Experiments - NFL Predictor";
  }, []);

  if (isLoading) {
    return (
      <div>
        <Skeleton className="h-7 w-48 mb-8" />
        <div className="flex flex-col gap-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-8 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    const notReady = error instanceof ApiError && error.isNotReady;
    return (
      <ErrorState
        heading={notReady ? "No Model Trained Yet" : "Connection Failed"}
        body={
          notReady
            ? "Run the training pipeline to generate experiment data."
            : "Could not reach the prediction API. Make sure the server is running."
        }
        onRetry={() => refetch()}
      />
    );
  }

  if (data && data.length === 0) {
    return (
      <div>
        <h1 className="text-xl font-semibold mb-8">Experiment Scoreboard</h1>
        <ErrorState
          heading="No Experiments Found"
          body="Run the training pipeline to generate experiment data."
        />
      </div>
    );
  }

  if (!data) return null;

  return (
    <div>
      <h1 className="text-xl font-semibold mb-8">Experiment Scoreboard</h1>
      <ExperimentTable experiments={data} />
    </div>
  );
}
