import { useEffect } from "react";

export function HistoryPage() {
  useEffect(() => {
    document.title = "History - NFL Predictor";
  }, []);

  return (
    <div>
      <h1 className="text-xl font-semibold">Prediction History</h1>
      <p className="text-sm text-muted-foreground">
        Prediction history will appear here.
      </p>
    </div>
  );
}
