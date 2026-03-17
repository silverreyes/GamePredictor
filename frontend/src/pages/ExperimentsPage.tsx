import { useEffect } from "react";

export function ExperimentsPage() {
  useEffect(() => {
    document.title = "Experiments - NFL Predictor";
  }, []);

  return (
    <div>
      <h1 className="text-xl font-semibold">Experiment Scoreboard</h1>
      <p className="text-sm text-muted-foreground">
        Experiment results will appear here.
      </p>
    </div>
  );
}
