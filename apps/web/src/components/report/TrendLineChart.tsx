"use client";

import type { EChartsOption } from "echarts";
import dynamic from "next/dynamic";

import { COLORS } from "@/lib/colors";
import { echarts } from "@/lib/echarts";
import type { TrendPoint } from "@/lib/types";

function withAlpha(hex: string, alpha: number): string {
  const a = Math.max(0, Math.min(255, Math.round(alpha * 255)))
    .toString(16)
    .padStart(2, "0");
  return `${hex}${a}`;
}

const ReactECharts = dynamic(() => import("echarts-for-react/lib/core"), {
  ssr: false,
});

type Props = {
  trend: TrendPoint[];
  color?: string;
  height?: number;
  min?: number;
  max?: number;
};

export function TrendLineChart({
  trend,
  color = COLORS.recBlue,
  height = 140,
  min = 0,
  max = 100,
}: Props) {
  const dates = trend.map((p) => p.date);
  const values = trend.map((p) => (p.value === null ? null : p.value));

  const option: EChartsOption = {
    animation: true,
    animationDuration: 600,
    grid: { top: 10, right: 10, bottom: 20, left: 30 },
    xAxis: {
      type: "category",
      data: dates,
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.15)" } },
      axisLabel: { show: false },
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      min,
      max,
      splitNumber: 4,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.05)" } },
      axisLabel: { color: COLORS.text3, fontSize: 10 },
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: COLORS.card,
      borderColor: "rgba(255,255,255,0.08)",
      textStyle: { color: COLORS.textPrimary, fontSize: 11 },
    },
    series: [
      {
        type: "line",
        data: values,
        smooth: true,
        showSymbol: false,
        lineStyle: { color, width: 2 },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: withAlpha(color, 0.33) },
              { offset: 1, color: withAlpha(color, 0) },
            ],
          },
        },
        connectNulls: false,
      },
    ],
  };

  return (
    <ReactECharts
      echarts={echarts}
      option={option}
      style={{ height, width: "100%" }}
      notMerge
      lazyUpdate
      opts={{ renderer: "canvas" }}
    />
  );
}
