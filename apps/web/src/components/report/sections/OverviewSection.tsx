import { Card } from "@/components/report/Card";
import { CardLabel } from "@/components/report/CardLabel";
import { DialRow } from "@/components/report/DialRow";
import { InsightCard } from "@/components/report/InsightCard";
import { MetricRow } from "@/components/report/MetricRow";
import type { Insight, WhoopReport } from "@/lib/types";

const SEVERITY_ORDER: Record<Insight["severity"], number> = {
  high: 0,
  medium: 1,
  low: 2,
};

export function OverviewSection({ report }: { report: WhoopReport }) {
  const topInsight =
    [...report.insights].sort(
      (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity],
    )[0] ?? null;
  return (
    <div className="flex flex-col gap-4">
      <DialRow dials={report.dials} />
      <Card>
        <CardLabel>Health monitor</CardLabel>
        <div className="mt-3">
          <MetricRow metrics={report.metrics} />
        </div>
      </Card>
      {topInsight ? <InsightCard insight={topInsight} /> : null}
    </div>
  );
}
