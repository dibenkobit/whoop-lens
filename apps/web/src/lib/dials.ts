import type { EChartsOption } from "echarts";

import { COLORS } from "./colors";

type DialInput = {
  value: number; // 0..max
  max: number;
  color: string;
  display: string; // text inside center, e.g., "68%"
  label: string; // UPPERCASE label below, e.g., "RECOVERY"
  sub?: string; // small text line under the label
};

export function buildDialOption(input: DialInput): EChartsOption {
  const pct = Math.max(0, Math.min(1, input.value / input.max));
  return {
    animation: true,
    animationDuration: 700,
    animationEasing: "cubicOut",
    series: [
      {
        type: "gauge",
        startAngle: 90,
        endAngle: -270,
        radius: "80%",
        center: ["50%", "52%"],
        progress: { show: true, width: 10, roundCap: true },
        pointer: { show: false },
        axisLine: {
          lineStyle: { width: 10, color: [[1, "rgba(255,255,255,0.08)"]] },
        },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        itemStyle: { color: input.color },
        title: { show: false },
        detail: { show: false },
        data: [{ value: pct * input.max }],
        min: 0,
        max: input.max,
        silent: true,
      },
    ],
    // Actual text rendering is handled in JSX; keep ECharts option purely visual
    textStyle: { color: COLORS.textPrimary, fontFamily: "var(--font-sans)" },
  };
}
