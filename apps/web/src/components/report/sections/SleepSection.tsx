import { Card } from "@/components/report/Card";
import { CardLabel } from "@/components/report/CardLabel";
import { ConsistencyStrip } from "@/components/report/ConsistencyStrip";
import { Dial } from "@/components/report/Dial";
import { Hypnogram } from "@/components/report/Hypnogram";
import { InsightCard } from "@/components/report/InsightCard";
import { SleepStageBreakdown } from "@/components/report/SleepStageBreakdown";
import { COLORS } from "@/lib/colors";
import type { Insight, WhoopReport } from "@/lib/types";

const SEVERITY_ORDER: Record<Insight["severity"], number> = {
  high: 0,
  medium: 1,
  low: 2,
};

export function SleepSection({ report }: { report: WhoopReport }) {
  const s = report.sleep;
  const sleepInsights = report.insights
    .filter((i) =>
      [
        "undersleep",
        "bedtime_consistency",
        "late_chronotype",
        "sleep_stage_quality",
      ].includes(i.kind),
    )
    .toSorted(
      (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity],
    );

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[260px_1fr]">
      <div className="flex flex-col gap-4">
        <Dial
          value={Math.min(report.dials.sleep.value, 12)}
          max={12}
          color={COLORS.sleep}
          display={`${report.dials.sleep.value.toFixed(2)}h`}
          label="Avg Sleep"
          sub={`${report.dials.sleep.performance_pct.toFixed(0)}% performance`}
        />
        <Card>
          <CardLabel>Schedule</CardLabel>
          <div className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-text-3">Avg bedtime</span>
              <span className="text-text-primary">
                {s.avg_bedtime}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-3">Avg wake</span>
              <span className="text-text-primary">{s.avg_wake}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-3">Bedtime std</span>
              <span className="text-text-primary">
                {s.bedtime_std_h.toFixed(1)}h
              </span>
            </div>
          </div>
        </Card>
      </div>
      <div className="flex flex-col gap-4">
        <Card>
          <CardLabel>Sleep stages</CardLabel>
          <div className="mt-3">
            <SleepStageBreakdown
              durations={s.avg_durations}
              pct={s.stage_pct}
            />
          </div>
        </Card>
        <Card>
          <CardLabel>Last night</CardLabel>
          <div className="mt-3">
            <Hypnogram night={s.hypnogram_sample} />
          </div>
        </Card>
        <Card>
          <CardLabel>Bedtime consistency · last 14 days</CardLabel>
          <div className="mt-3">
            <ConsistencyStrip strip={s.consistency_strip} />
          </div>
        </Card>
        {sleepInsights.slice(0, 2).map((i) => (
          <InsightCard key={i.kind} insight={i} />
        ))}
      </div>
    </div>
  );
}
