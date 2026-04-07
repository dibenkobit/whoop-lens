import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

import { ApiError, analyzeZip, createShare, getSharedReport } from "@/lib/api";
import type { WhoopReport } from "@/lib/types";

const mockReport: WhoopReport = {
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

describe("api", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("analyzeZip posts multipart and returns the report on 200", async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify(mockReport), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const file = new File(["zip"], "my.zip", { type: "application/zip" });
    const out = await analyzeZip(file);
    expect(out.schema_version).toBe(1);
    expect(global.fetch).toHaveBeenCalledOnce();
    const call = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(call?.[0]).toMatch(/\/analyze$/);
  });

  it("analyzeZip throws ApiError on 400 with body", async () => {
    const makeResponse = () =>
      new Response(JSON.stringify({ code: "not_a_zip" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    (global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce(makeResponse())
      .mockResolvedValueOnce(makeResponse());
    const file = new File(["nope"], "bad.txt");
    await expect(analyzeZip(file)).rejects.toBeInstanceOf(ApiError);
    try {
      await analyzeZip(file);
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as ApiError).status).toBe(400);
      expect((e as ApiError).body?.code).toBe("not_a_zip");
    }
  });

  it("createShare posts JSON and returns the share record", async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "abc12345",
          url: "/r/abc12345",
          expires_at: "2026-05-07T00:00:00Z",
        }),
        { status: 201, headers: { "Content-Type": "application/json" } },
      ),
    );
    const out = await createShare(mockReport);
    expect(out.id).toBe("abc12345");
  });

  it("getSharedReport returns null on 404", async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response("", { status: 404 }),
    );
    const out = await getSharedReport("nothere");
    expect(out).toBeNull();
  });

  it("getSharedReport returns the report on 200", async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify(mockReport), { status: 200 }),
    );
    const out = await getSharedReport("abc12345");
    expect(out?.schema_version).toBe(1);
  });
});
