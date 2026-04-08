import { Card } from "@/components/report/Card";
import { CardLabel } from "@/components/report/CardLabel";
import { Dial } from "@/components/report/Dial";
import { InsightCard } from "@/components/report/InsightCard";
import { StrainDistribution } from "@/components/report/StrainDistribution";
import { TrendLineChart } from "@/components/report/TrendLineChart";
import { COLORS } from "@/lib/colors";
import type { WhoopReport } from "@/lib/types";

export function StrainSection({ report }: { report: WhoopReport }) {
  const d = report.dials.strain;
  const strainInsights = report.insights.filter((i) =>
    ["overtraining", "workout_mix"].includes(i.kind),
  );
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[260px_1fr]">
      <div className="flex flex-col gap-4">
        <Dial
          value={d.value}
          max={21}
          color={COLORS.strain}
          display={d.value.toFixed(1)}
          label="Avg Strain"
          sub={d.label.replace("_", " ")}
        />
      </div>
      <div className="flex flex-col gap-4">
        <Card>
          <CardLabel>Strain trend</CardLabel>
          <div className="mt-3">
            <TrendLineChart
              trend={report.strain.trend}
              color={COLORS.strain}
              max={21}
            />
          </div>
        </Card>
        <Card>
          <CardLabel>Distribution by zone</CardLabel>
          <div className="mt-3">
            <StrainDistribution distribution={report.strain.distribution} />
          </div>
        </Card>
        {strainInsights.map((i) => (
          <InsightCard key={i.kind} insight={i} />
        ))}
      </div>
    </div>
  );
}
