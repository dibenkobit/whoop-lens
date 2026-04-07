"use client";

import dynamic from "next/dynamic";

import { buildDialOption } from "@/lib/dials";
import { echarts } from "@/lib/echarts";

const ReactECharts = dynamic(() => import("echarts-for-react/lib/core"), {
  ssr: false,
  loading: () => (
    <div className="h-[140px] w-[140px] animate-pulse rounded-full bg-white/5" />
  ),
});

type Props = {
  value: number;
  max: number;
  color: string;
  display: string;
  label: string;
  sub?: string;
};

export function Dial({ value, max, color, display, label, sub }: Props) {
  const option = buildDialOption({ value, max, color, display, label, sub });
  return (
    <div
      data-testid="dial"
      className="relative flex flex-col items-center justify-center rounded-2xl bg-card px-4 py-5"
    >
      <div className="relative h-[140px] w-[140px]">
        <ReactECharts
          echarts={echarts}
          option={option}
          style={{ height: 140, width: 140 }}
          notMerge
          lazyUpdate
          opts={{ renderer: "canvas" }}
        />
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <span className="font-mono text-3xl font-bold tracking-tight text-text-primary">
            {display}
          </span>
        </div>
      </div>
      <div className="mt-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-text-3">
        {label}
      </div>
      {sub ? <div className="mt-1 text-[11px] text-text-2">{sub}</div> : null}
    </div>
  );
}
