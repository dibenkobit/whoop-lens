import { recoveryColor } from "@/lib/colors";
import { formatHoursDecimal, formatPct } from "@/lib/format";
import type { MonthlyAgg } from "@/lib/types";

export function MonthlyHeatmap({ monthly }: { monthly: MonthlyAgg[] }) {
  if (monthly.length === 0) {
    return (
      <p className="text-sm text-text-3">Not enough data for monthly trends.</p>
    );
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] text-xs">
        <thead>
          <tr className="text-[10px] uppercase tracking-[0.12em] text-text-3">
            <th className="text-left">Month</th>
            <th className="text-right">Recovery</th>
            <th className="text-right">HRV</th>
            <th className="text-right">RHR</th>
            <th className="text-right">Sleep</th>
          </tr>
        </thead>
        <tbody>
          {monthly.map((m) => (
            <tr key={m.month} className="border-t border-white/5">
              <td className="py-2 text-text-2">{m.month}</td>
              <td
                className="py-2 text-right font-bold"
                style={{ color: recoveryColor(m.recovery) }}
              >
                {formatPct(m.recovery)}
              </td>
              <td className="py-2 text-right text-text-primary">
                {m.hrv.toFixed(0)}
              </td>
              <td className="py-2 text-right text-text-primary">
                {m.rhr.toFixed(1)}
              </td>
              <td className="py-2 text-right text-text-primary">
                {formatHoursDecimal(m.sleep_h, 2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
