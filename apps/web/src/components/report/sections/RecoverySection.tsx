import { Card } from "@/components/report/Card";
import { CardLabel } from "@/components/report/CardLabel";
import { Dial } from "@/components/report/Dial";
import { DowBars } from "@/components/report/DowBars";
import { InsightCard } from "@/components/report/InsightCard";
import { RecoveryDistribution } from "@/components/report/RecoveryDistribution";
import { SickEpisodesList } from "@/components/report/SickEpisodesList";
import { TrendLineChart } from "@/components/report/TrendLineChart";
import { COLORS, recoveryColor } from "@/lib/colors";
import type { Insight, WhoopReport } from "@/lib/types";

const SEVERITY_ORDER: Record<Insight["severity"], number> = {
  high: 0,
  medium: 1,
  low: 2,
};

export function RecoverySection({ report }: { report: WhoopReport }) {
  const rec = report.dials.recovery;
  const recoveryInsights = report.insights
    .filter((i) =>
      [
        "sick_episodes",
        "dow_pattern",
        "travel_impact",
        "long_term_trend",
      ].includes(i.kind),
    )
    .toSorted(
      (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity],
    );
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[260px_1fr]">
      <div className="flex flex-col gap-4">
        <Dial
          value={rec.value}
          max={100}
          color={recoveryColor(rec.value)}
          display={`${rec.value.toFixed(0)}%`}
          label="Avg Recovery"
          sub={`${rec.green_pct.toFixed(0)}% green days`}
        />
        <Card>
          <CardLabel>Distribution</CardLabel>
          <div className="mt-3">
            <RecoveryDistribution distribution={report.recovery.distribution} />
          </div>
        </Card>
      </div>
      <div className="flex flex-col gap-4">
        <Card>
          <CardLabel>Recovery trend</CardLabel>
          <div className="mt-3">
            <TrendLineChart
              trend={report.recovery.trend}
              color={COLORS.recBlue}
            />
          </div>
        </Card>
        <Card>
          <CardLabel>Day of week</CardLabel>
          <div className="mt-3">
            <DowBars entries={report.recovery.by_dow} />
          </div>
        </Card>
        <Card>
          <CardLabel>Likely illness episodes</CardLabel>
          <div className="mt-3">
            <SickEpisodesList episodes={report.recovery.sick_episodes} />
          </div>
        </Card>
        {recoveryInsights.slice(0, 2).map((i) => (
          <InsightCard key={i.kind} insight={i} />
        ))}
      </div>
    </div>
  );
}
