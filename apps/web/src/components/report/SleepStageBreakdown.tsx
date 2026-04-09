import { COLORS } from "@/lib/colors";
import { formatHours } from "@/lib/format";
import type { SleepDurations, SleepStagePct } from "@/lib/types";

type Props = {
  durations: SleepDurations;
  pct: SleepStagePct;
};

export function SleepStageBreakdown({ durations, pct }: Props) {
  const rows: {
    label: string;
    pct: number;
    minutes: number;
    tone: string;
  }[] = [
    {
      label: "Deep",
      pct: pct.deep,
      minutes: durations.deep_min,
      tone: COLORS.sleep,
    },
    {
      label: "REM",
      pct: pct.rem,
      minutes: durations.rem_min,
      tone: `${COLORS.sleep}cc`,
    },
    {
      label: "Light",
      pct: pct.light,
      minutes: durations.light_min,
      tone: `${COLORS.sleep}80`,
    },
    {
      label: "Awake",
      pct: 0, // derived from stages not explicitly, omit from bar
      minutes: durations.awake_min,
      tone: `${COLORS.sleep}40`,
    },
  ];
  return (
    <div className="space-y-3">
      {rows.map((r) => (
        <div key={r.label}>
          <div className="flex justify-between text-[11px] text-text-2">
            <span>{r.label}</span>
            <span>
              {formatHours(r.minutes)}
              {r.pct > 0 ? (
                <span className="ml-2 text-text-3">{r.pct.toFixed(0)}%</span>
              ) : null}
            </span>
          </div>
          <div className="mt-1 h-1.5 w-full rounded-full bg-black/40">
            <div
              className="h-full rounded-full"
              style={{
                width: `${Math.min(r.pct, 100)}%`,
                backgroundColor: r.tone,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
