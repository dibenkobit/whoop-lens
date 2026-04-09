import { recoveryColor } from "@/lib/colors";
import { formatDate } from "@/lib/format";
import type { TopStrainDay } from "@/lib/types";

export function TopStrainDays({ days }: { days: TopStrainDay[] }) {
  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="text-[10px] uppercase tracking-[0.14em] text-text-3">
          <th className="text-left">Date</th>
          <th className="text-right">Strain</th>
          <th className="text-right">Rec</th>
          <th className="text-right">Next</th>
        </tr>
      </thead>
      <tbody>
        {days.map((d) => (
          <tr key={d.date} className="border-t border-white/5">
            <td className="py-1.5 text-text-2">{formatDate(d.date)}</td>
            <td className="py-1.5 text-right text-text-primary">
              {d.day_strain.toFixed(1)}
            </td>
            <td
              className="py-1.5 text-right"
              style={{ color: recoveryColor(d.recovery) }}
            >
              {d.recovery.toFixed(0)}%
            </td>
            <td
              className="py-1.5 text-right"
              style={{
                color:
                  d.next_recovery === null
                    ? "var(--color-text-3)"
                    : recoveryColor(d.next_recovery),
              }}
            >
              {d.next_recovery === null
                ? "—"
                : `${d.next_recovery.toFixed(0)}%`}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
