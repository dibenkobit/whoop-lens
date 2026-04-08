"use client";

import { COLORS } from "@/lib/colors";
import type { HypnogramNight, HypnogramStage } from "@/lib/types";

const STAGE_ROW: Record<HypnogramStage, number> = {
  awake: 0,
  rem: 1,
  light: 2,
  deep: 3,
};
const STAGE_LABEL: Record<HypnogramStage, string> = {
  awake: "Awake",
  rem: "REM",
  light: "Light",
  deep: "Deep",
};
const STAGE_COLOR: Record<HypnogramStage, string> = {
  awake: `${COLORS.sleep}40`,
  rem: `${COLORS.sleep}80`,
  light: `${COLORS.sleep}bb`,
  deep: COLORS.sleep,
};

type Props = {
  night: HypnogramNight | null;
};

export function Hypnogram({ night }: Props) {
  if (!night || night.segments.length === 0) {
    return (
      <p className="text-sm text-text-3">
        Per-night stage timeline isn't available in your export.
      </p>
    );
  }
  const start = new Date(night.start).getTime();
  const end = new Date(night.end).getTime();
  const span = Math.max(end - start, 1);

  return (
    <div className="relative h-28 w-full">
      {/* rows background */}
      <div className="absolute inset-0 flex flex-col justify-between">
        {(["awake", "rem", "light", "deep"] as HypnogramStage[]).map((s) => (
          <div
            key={s}
            className="h-[22%] border-t border-white/5 text-[9px] text-text-3"
          >
            {STAGE_LABEL[s]}
          </div>
        ))}
      </div>
      {/* segments */}
      {night.segments.map((seg) => {
        const t0 = new Date(seg.from).getTime();
        const t1 = new Date(seg.to).getTime();
        const left = ((t0 - start) / span) * 100;
        const width = ((t1 - t0) / span) * 100;
        const row = STAGE_ROW[seg.stage];
        return (
          <div
            key={`${seg.from}-${seg.stage}`}
            className="absolute h-[16%] rounded-sm"
            style={{
              left: `${left}%`,
              width: `${width}%`,
              top: `${row * 22 + 3}%`,
              backgroundColor: STAGE_COLOR[seg.stage],
            }}
          />
        );
      })}
    </div>
  );
}
