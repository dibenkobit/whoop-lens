import { formatDate } from "@/lib/format";
import type { SickEpisode } from "@/lib/types";

export function SickEpisodesList({ episodes }: { episodes: SickEpisode[] }) {
  if (episodes.length === 0) {
    return (
      <p className="text-sm text-text-3">
        No illness-like episodes detected in your data. Nice.
      </p>
    );
  }
  return (
    <ul className="space-y-2">
      {episodes.map((e) => (
        <li
          key={e.date}
          className="flex items-center justify-between rounded-md bg-black/30 px-3 py-2 text-xs"
        >
          <span className="font-mono text-text-primary">
            {formatDate(e.date)}
          </span>
          <span className="text-text-2">
            rec {e.recovery.toFixed(0)}% · rhr {Math.round(e.rhr)} · hrv{" "}
            {Math.round(e.hrv)}
            {e.skin_temp_c !== null
              ? ` · skin ${e.skin_temp_c.toFixed(1)}°C`
              : ""}
          </span>
        </li>
      ))}
    </ul>
  );
}
