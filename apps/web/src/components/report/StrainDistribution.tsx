import { COLORS } from "@/lib/colors";
import type { StrainDistribution as DistType } from "@/lib/types";

const ROWS: {
  key: keyof DistType;
  label: string;
  hint: string;
  tint: number;
}[] = [
  { key: "light", label: "Light", hint: "0–9", tint: 0.4 },
  { key: "moderate", label: "Moderate", hint: "10–13", tint: 0.65 },
  { key: "high", label: "High", hint: "14–17", tint: 0.85 },
  { key: "all_out", label: "All Out", hint: "18–21", tint: 1 },
];

export function StrainDistribution({
  distribution,
}: {
  distribution: DistType;
}) {
  return (
    <div className="space-y-2">
      {ROWS.map((row) => {
        const value = distribution[row.key];
        return (
          <div key={row.key} className="flex items-center gap-3 text-xs">
            <div className="w-20 text-text-3">{row.label}</div>
            <div className="relative h-2 flex-1 overflow-hidden rounded-sm bg-black/40">
              <div
                className="h-full rounded-sm"
                style={{
                  width: `${value}%`,
                  backgroundColor: COLORS.strain,
                  opacity: row.tint,
                }}
              />
            </div>
            <div className="w-10 text-right font-mono text-text-2">
              {value.toFixed(0)}%
            </div>
            <div className="w-12 text-text-3">{row.hint}</div>
          </div>
        );
      })}
    </div>
  );
}
