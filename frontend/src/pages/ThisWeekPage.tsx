import { useEffect } from "react";

export function ThisWeekPage() {
  useEffect(() => {
    document.title = "Week Picks - NFL Predictor";
  }, []);

  return (
    <div>
      <h1 className="text-xl font-semibold">Week Picks</h1>
      <p className="text-sm text-muted-foreground">
        This week's predictions will appear here.
      </p>
    </div>
  );
}
