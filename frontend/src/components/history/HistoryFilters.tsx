import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface HistoryFiltersProps {
  season: number | undefined;
  team: string | undefined;
  onSeasonChange: (season: number | undefined) => void;
  onTeamChange: (team: string | undefined) => void;
  availableSeasons: number[];
  availableTeams: string[];
}

export function HistoryFilters({
  season,
  team,
  onSeasonChange,
  onTeamChange,
  availableSeasons,
  availableTeams,
}: HistoryFiltersProps) {
  return (
    <div className="flex gap-4 mb-6">
      <Select
        value={season !== undefined ? String(season) : "all"}
        onValueChange={(val: string | null) => {
          onSeasonChange(!val || val === "all" ? undefined : Number(val));
        }}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="All Seasons" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Seasons</SelectItem>
          {availableSeasons.map((s) => (
            <SelectItem key={s} value={String(s)}>
              {s}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={team !== undefined ? team : "all"}
        onValueChange={(val: string | null) => {
          onTeamChange(!val || val === "all" ? undefined : val);
        }}
      >
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="All Teams" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Teams</SelectItem>
          {availableTeams.map((t) => (
            <SelectItem key={t} value={t}>
              {t}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
