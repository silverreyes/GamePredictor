import { CircleCheck, CircleX, Minus } from "lucide-react";

interface ResultIndicatorProps {
  correct: boolean | null;
}

export function ResultIndicator({ correct }: ResultIndicatorProps) {
  if (correct === true) {
    return <CircleCheck className="h-5 w-5 text-green-500" />;
  }

  if (correct === false) {
    return <CircleX className="h-5 w-5 text-red-500" />;
  }

  return (
    <span className="flex items-center gap-1">
      <Minus className="h-5 w-5 text-zinc-500" />
      <span className="text-xs text-muted-foreground">Pending</span>
    </span>
  );
}
