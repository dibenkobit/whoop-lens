import { describe, expectTypeOf, it } from "vitest";

import type {
  Insight,
  InsightKind,
  InsightSeverity,
  ShareCreateRequest,
  ShareCreateResponse,
  WhoopReport,
} from "@/lib/types";

describe("types contract", () => {
  it("WhoopReport has the top-level sections", () => {
    // compile-time contract: assignability checks
    const example: WhoopReport = {
      schema_version: 1,
      period: { start: "2025-01-01", end: "2025-01-31", days: 31 },
      dials: {
        sleep: { value: 8, unit: "h", performance_pct: 85 },
        recovery: { value: 70, unit: "%", green_pct: 60 },
        strain: { value: 10, unit: "", label: "moderate" },
      },
      metrics: {
        hrv_ms: 120,
        rhr_bpm: 50,
        resp_rpm: 15,
        spo2_pct: 95,
        sleep_efficiency_pct: 92,
        sleep_consistency_pct: 60,
        sleep_debt_min: 20,
      },
      recovery: {
        trend: [],
        by_dow: [],
        distribution: { green: 60, yellow: 35, red: 5 },
        sick_episodes: [],
      },
      sleep: {
        avg_bedtime: "02:22",
        avg_wake: "11:36",
        bedtime_std_h: 1.5,
        avg_durations: {
          light_min: 270,
          rem_min: 110,
          deep_min: 100,
          awake_min: 38,
        },
        stage_pct: { light: 56, rem: 22, deep: 22 },
        hypnogram_sample: null,
        consistency_strip: [],
      },
      strain: {
        avg_strain: 10,
        distribution: { light: 50, moderate: 40, high: 9, all_out: 1 },
        trend: [],
      },
      workouts: null,
      journal: null,
      trends: {
        monthly: [],
        first_vs_last_60d: {
          bedtime_h: [26.5, 25.5],
          sleep_h: [7.5, 8.0],
          rhr: [52, 50],
          workouts: [15, 30],
        },
      },
      insights: [],
    };
    expectTypeOf(example).toMatchTypeOf<WhoopReport>();
  });

  it("InsightKind has the 10 kinds", () => {
    const kinds: InsightKind[] = [
      "undersleep",
      "bedtime_consistency",
      "late_chronotype",
      "overtraining",
      "sick_episodes",
      "travel_impact",
      "dow_pattern",
      "sleep_stage_quality",
      "long_term_trend",
      "workout_mix",
    ];
    expectTypeOf(kinds).toEqualTypeOf<InsightKind[]>();
  });

  it("InsightSeverity has three levels", () => {
    const levels: InsightSeverity[] = ["low", "medium", "high"];
    expectTypeOf(levels).toEqualTypeOf<InsightSeverity[]>();
  });

  it("Insight.highlight.unit is optional (absent, not null)", () => {
    const insight: Insight = {
      kind: "undersleep",
      severity: "medium",
      title: "t",
      body: "b",
      highlight: { value: "+30" }, // no unit — absent, not null
    };
    expectTypeOf(insight).toMatchTypeOf<Insight>();
  });

  it("Share types exist", () => {
    const req: ShareCreateRequest = {
      report: {} as WhoopReport,
    };
    const res: ShareCreateResponse = {
      id: "abc12345",
      url: "/r/abc12345",
      expires_at: "2026-05-07T00:00:00Z",
    };
    expectTypeOf(req).toMatchTypeOf<ShareCreateRequest>();
    expectTypeOf(res).toMatchTypeOf<ShareCreateResponse>();
  });
});
