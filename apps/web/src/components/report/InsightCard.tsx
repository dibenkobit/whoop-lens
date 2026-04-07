import type { Insight } from "@/lib/types";

import { Card } from "./Card";

const LABELS: Record<Insight["severity"], string> = {
  high: "HIGH PRIORITY",
  medium: "WORTH NOTICING",
  low: "OBSERVATION",
};

export function InsightCard({ insight }: { insight: Insight }) {
  return (
    <Card className="flex flex-col gap-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-teal">
        {LABELS[insight.severity]}
      </div>
      <h3 className="text-base font-semibold leading-snug text-text-primary">
        {insight.title}
      </h3>
      <div className="flex items-baseline gap-2">
        <span className="font-mono text-2xl font-bold text-text-primary">
          {insight.highlight.value}
        </span>
        {insight.highlight.unit ? (
          <span className="text-[11px] uppercase tracking-[0.15em] text-text-3">
            {insight.highlight.unit}
          </span>
        ) : null}
      </div>
      <p className="text-sm leading-relaxed text-text-2">{insight.body}</p>
    </Card>
  );
}
