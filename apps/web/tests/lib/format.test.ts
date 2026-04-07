import { describe, it, expect } from "vitest";

import {
  clockFrom24h,
  formatBpm,
  formatDate,
  formatDelta,
  formatHours,
  formatHoursDecimal,
  formatMs,
  formatPct,
  formatPeriod,
} from "@/lib/format";

describe("format", () => {
  it("formatPct", () => {
    expect(formatPct(68.82, 0)).toBe("69%");
    expect(formatPct(68.82, 1)).toBe("68.8%");
  });

  it("formatHours", () => {
    expect(formatHours(476)).toBe("7h 56m");
    expect(formatHours(60)).toBe("1h 0m");
  });

  it("formatHoursDecimal", () => {
    expect(formatHoursDecimal(7.96)).toBe("8.0h");
    expect(formatHoursDecimal(7.96, 2)).toBe("7.96h");
  });

  it("formatBpm + formatMs", () => {
    expect(formatBpm(50.4)).toBe("50 bpm");
    expect(formatMs(123.7)).toBe("124 ms");
  });

  it("formatDelta includes sign", () => {
    expect(formatDelta(30)).toBe("+30 pp");
    expect(formatDelta(-7)).toBe("-7 pp");
    expect(formatDelta(0)).toBe("+0 pp");
  });

  it("formatDate parses ISO and uses locale", () => {
    expect(formatDate("2025-01-15")).toMatch(/Jan/);
  });

  it("formatDate returns input on malformed ISO", () => {
    expect(formatDate("not-a-date")).toBe("not-a-date");
  });

  it("formatPeriod joins two dates", () => {
    const out = formatPeriod("2025-01-01", "2025-03-31");
    expect(out).toContain("Jan");
    expect(out).toContain("Mar");
  });

  it("clockFrom24h wraps past midnight", () => {
    expect(clockFrom24h(23.5)).toBe("23:30");
    expect(clockFrom24h(25.0)).toBe("01:00");
    expect(clockFrom24h(28.75)).toBe("04:45");
  });

  it("formatHours wraps when minutes round up to 60", () => {
    expect(formatHours(119.6)).toBe("2h 0m");
    expect(formatHours(59.6)).toBe("1h 0m");
  });
});
