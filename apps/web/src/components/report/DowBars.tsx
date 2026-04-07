import { COLORS, recoveryColor } from "@/lib/colors";
import type { DowEntry } from "@/lib/types";

const ORDER = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"] as const;
const LABELS: Record<(typeof ORDER)[number], string> = {
  mon: "MON",
  tue: "TUE",
  wed: "WED",
  thu: "THU",
  fri: "FRI",
  sat: "SAT",
  sun: "SUN",
};

type Props = { entries: DowEntry[] };

export function DowBars({ entries }: Props) {
  const byDow = new Map(entries.map((e) => [e.dow, e]));
  const max = Math.max(...entries.map((e) => e.mean), 1);

  return (
    <div className="grid grid-cols-7 gap-2">
      {ORDER.map((dow) => {
        const e = byDow.get(dow);
        const value = e?.mean ?? 0;
        const heightPct = (value / 100) * 100; // 0-100
        const color = e ? recoveryColor(value) : COLORS.text3;
        const dim = value < max * 0.7;
        return (
          <div key={dow} className="flex flex-col items-center gap-2">
            <div className="relative h-16 w-full">
              <div
                className="absolute inset-x-0 bottom-0 rounded-sm"
                style={{
                  backgroundColor: color,
                  height: `${Math.max(heightPct, 2)}%`,
                  opacity: dim ? 0.65 : 1,
                }}
              />
            </div>
            <div className="text-[9px] tracking-[0.1em] text-text-3">
              {LABELS[dow]}
            </div>
          </div>
        );
      })}
    </div>
  );
}
