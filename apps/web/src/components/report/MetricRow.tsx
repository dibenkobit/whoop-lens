import type { Metrics } from "@/lib/types";

type Item = { label: string; value: string; unit?: string };

function Cell({ item }: { item: Item }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-[0.18em] text-text-3">
        {item.label}
      </div>
      <div className="mt-1 text-base font-bold text-text-primary">
        {item.value}
        {item.unit ? (
          <span className="ml-1 text-xs font-normal text-text-3">
            {item.unit}
          </span>
        ) : null}
      </div>
    </div>
  );
}

export function MetricRow({ metrics }: { metrics: Metrics }) {
  const items: Item[] = [
    { label: "HRV", value: Math.round(metrics.hrv_ms).toString(), unit: "ms" },
    {
      label: "RHR",
      value: Math.round(metrics.rhr_bpm).toString(),
      unit: "bpm",
    },
    { label: "Resp", value: metrics.resp_rpm.toFixed(1) },
    {
      label: "SpO₂",
      value: metrics.spo2_pct.toFixed(1),
      unit: "%",
    },
  ];
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {items.map((it) => (
        <Cell key={it.label} item={it} />
      ))}
    </div>
  );
}
