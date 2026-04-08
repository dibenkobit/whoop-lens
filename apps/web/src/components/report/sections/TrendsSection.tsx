import { Card } from "@/components/report/Card";
import { CardLabel } from "@/components/report/CardLabel";
import { FirstVsLast } from "@/components/report/FirstVsLast";
import { InsightCard } from "@/components/report/InsightCard";
import { MonthlyHeatmap } from "@/components/report/MonthlyHeatmap";
import type { WhoopReport } from "@/lib/types";

export function TrendsSection({ report }: { report: WhoopReport }) {
  const trendInsights = report.insights.filter((i) =>
    ["long_term_trend"].includes(i.kind),
  );
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardLabel>Month by month</CardLabel>
        <div className="mt-3">
          <MonthlyHeatmap monthly={report.trends.monthly} />
        </div>
      </Card>
      <Card>
        <CardLabel>First 60 days vs last 60 days</CardLabel>
        <div className="mt-3">
          <FirstVsLast comparison={report.trends.first_vs_last_60d} />
        </div>
      </Card>
      {trendInsights.map((i) => (
        <InsightCard key={i.kind} insight={i} />
      ))}
    </div>
  );
}
