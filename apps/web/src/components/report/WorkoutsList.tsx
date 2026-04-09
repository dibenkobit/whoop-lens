import { formatHours } from "@/lib/format";
import type { ActivityAgg } from "@/lib/types";

export function WorkoutsList({ items }: { items: ActivityAgg[] }) {
  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li
          key={item.name}
          className="grid grid-cols-[1fr_80px_80px_60px] items-center gap-3 text-xs"
        >
          <div className="truncate text-text-primary">{item.name}</div>
          <div className="text-right text-text-2">{item.count}×</div>
          <div className="text-right text-text-2">
            {formatHours(item.total_min)}
          </div>
          <div className="text-right text-text-3">
            {item.pct_of_total_strain.toFixed(0)}%
          </div>
        </li>
      ))}
    </ul>
  );
}
