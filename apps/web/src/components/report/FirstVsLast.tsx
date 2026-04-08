import type { TrendComparison } from "@/lib/types";

type Row = {
  label: string;
  first: string;
  last: string;
  delta: string;
  betterIfHigher: boolean;
  numericDelta: number;
};

function arrowColor(positive: boolean): string {
  return positive ? "var(--color-rec-green)" : "var(--color-rec-red)";
}

export function FirstVsLast({ comparison }: { comparison: TrendComparison }) {
  const rows: Row[] = [
    {
      label: "Bedtime (hours past noon)",
      first: comparison.bedtime_h[0].toFixed(2),
      last: comparison.bedtime_h[1].toFixed(2),
      delta: (comparison.bedtime_h[1] - comparison.bedtime_h[0]).toFixed(2),
      betterIfHigher: false, // earlier bedtime = lower number = better
      numericDelta: comparison.bedtime_h[1] - comparison.bedtime_h[0],
    },
    {
      label: "Sleep duration",
      first: `${comparison.sleep_h[0].toFixed(2)}h`,
      last: `${comparison.sleep_h[1].toFixed(2)}h`,
      delta: `${(comparison.sleep_h[1] - comparison.sleep_h[0]).toFixed(2)}h`,
      betterIfHigher: true,
      numericDelta: comparison.sleep_h[1] - comparison.sleep_h[0],
    },
    {
      label: "Resting HR",
      first: `${comparison.rhr[0].toFixed(1)} bpm`,
      last: `${comparison.rhr[1].toFixed(1)} bpm`,
      delta: `${(comparison.rhr[1] - comparison.rhr[0]).toFixed(1)}`,
      betterIfHigher: false,
      numericDelta: comparison.rhr[1] - comparison.rhr[0],
    },
    {
      label: "Workouts (60d window)",
      first: comparison.workouts[0].toString(),
      last: comparison.workouts[1].toString(),
      delta: (comparison.workouts[1] - comparison.workouts[0]).toString(),
      betterIfHigher: true,
      numericDelta: comparison.workouts[1] - comparison.workouts[0],
    },
  ];
  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="text-[10px] uppercase tracking-[0.12em] text-text-3">
          <th className="text-left">Metric</th>
          <th className="text-right">First 60 days</th>
          <th className="text-right">Last 60 days</th>
          <th className="text-right">Δ</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => {
          const improved = row.betterIfHigher
            ? row.numericDelta > 0
            : row.numericDelta < 0;
          return (
            <tr key={row.label} className="border-t border-white/5">
              <td className="py-2 text-text-2">{row.label}</td>
              <td className="py-2 text-right font-mono text-text-3">
                {row.first}
              </td>
              <td className="py-2 text-right font-mono text-text-primary">
                {row.last}
              </td>
              <td
                className="py-2 text-right font-mono font-bold"
                style={{ color: arrowColor(improved) }}
              >
                {row.numericDelta >= 0 ? "+" : ""}
                {row.delta}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
