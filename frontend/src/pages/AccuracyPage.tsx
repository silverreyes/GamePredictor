import { useEffect } from "react";

export function AccuracyPage() {
  useEffect(() => {
    document.title = "Season Accuracy - NFL Predictor";
  }, []);

  return (
    <div>
      <h1 className="text-xl font-semibold">Season Accuracy</h1>
      <p className="text-sm text-muted-foreground">
        Season accuracy summary will appear here.
      </p>
    </div>
  );
}
