import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const tierStyles: Record<string, string> = {
  high: "bg-blue-500/20 text-blue-400",
  medium: "bg-amber-500/20 text-amber-400",
  low: "bg-zinc-500/20 text-zinc-400",
};

interface ConfidenceBadgeProps {
  tier: "high" | "medium" | "low";
}

export function ConfidenceBadge({ tier }: ConfidenceBadgeProps) {
  const label = tier.charAt(0).toUpperCase() + tier.slice(1);

  return (
    <Badge
      variant="outline"
      className={cn("border-0 text-xs", tierStyles[tier])}
    >
      {label}
    </Badge>
  );
}
