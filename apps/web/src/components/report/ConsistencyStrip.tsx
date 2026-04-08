import { COLORS } from "@/lib/colors";
import type { BedtimeStrip } from "@/lib/types";

type Props = { strip: BedtimeStrip[] };

// Convert "HH:MM" to hours past noon (bedtime) or hours past midnight (wake).
// Bedtime: 12:00-23:59 -> 0..11.99, 00:00-11:59 -> 12..23.99 (day-aligned 12-36h)
// We render on a 24h strip starting at 18:00 and ending at 14:00 next day.
function bedHours(hhmm: string): number {
  const [h, m] = hhmm.split(":").map(Number);
  const raw = (h ?? 0) + (m ?? 0) / 60;
  return raw >= 12 ? raw : raw + 24;
}

function wakeHours(hhmm: string): number {
  const [h, m] = hhmm.split(":").map(Number);
  const raw = (h ?? 0) + (m ?? 0) / 60;
  return raw < 12 ? raw + 24 : raw; // always treat wake as next day
}

const STRIP_START = 18; // 6pm
const STRIP_END = 38; // 2pm next day = 14+24
const STRIP_SPAN = STRIP_END - STRIP_START;

export function ConsistencyStrip({ strip }: Props) {
  if (strip.length === 0) {
    return <p className="text-sm text-text-3">Not enough data yet.</p>;
  }
  return (
    <div className="space-y-1.5">
      {strip.map((row) => {
        const bed = bedHours(row.bed_local);
        const wake = wakeHours(row.wake_local);
        const leftPct = ((bed - STRIP_START) / STRIP_SPAN) * 100;
        const widthPct = ((wake - bed) / STRIP_SPAN) * 100;
        const clampedLeft = Math.max(leftPct, 0);
        const clampedWidth = Math.max(Math.min(widthPct, 100 - clampedLeft), 0);
        return (
          <div key={row.date} className="flex items-center gap-3">
            <div className="w-14 text-[10px] text-text-3">
              {row.date.slice(5)}
            </div>
            <div className="relative h-3 flex-1 overflow-hidden rounded-sm bg-black/40">
              <div
                className="absolute inset-y-0"
                style={{
                  left: `${clampedLeft}%`,
                  width: `${clampedWidth}%`,
                  backgroundColor: COLORS.sleep,
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
