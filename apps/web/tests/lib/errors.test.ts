import { describe, it, expect } from "vitest";

import { friendlyError } from "@/lib/errors";

describe("friendlyError", () => {
  it("handles file_too_large", () => {
    const err = friendlyError({ code: "file_too_large", limit_mb: 50 }, 413);
    expect(err.title).toMatch(/too large/i);
    expect(err.description).toContain("50");
    expect(err.canRetry).toBe(false);
  });

  it("handles not_a_zip", () => {
    const err = friendlyError({ code: "not_a_zip" }, 400);
    expect(err.title).toMatch(/whoop export/i);
  });

  it("handles missing_required_file with filename", () => {
    const err = friendlyError(
      { code: "missing_required_file", file: "physiological_cycles.csv" },
      400,
    );
    expect(err.title).toContain("physiological_cycles.csv");
  });

  it("handles 5xx with error_id", () => {
    const err = friendlyError(
      { code: "analysis_failed", error_id: "abc123" },
      500,
    );
    expect(err.description).toContain("abc123");
    expect(err.canRetry).toBe(true);
  });

  it("falls back on unknown code", () => {
    const err = friendlyError({ code: "weird_thing" }, 400);
    expect(err.description).toContain("weird_thing");
  });

  it("falls back on null body", () => {
    const err = friendlyError(null, 400);
    expect(err.title).toMatch(/upload failed/i);
  });
});
