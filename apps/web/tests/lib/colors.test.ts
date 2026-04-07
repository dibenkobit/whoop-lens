import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";

import { COLORS, recoveryColor } from "@/lib/colors";

describe("colors", () => {
  it("recoveryColor matches Whoop thresholds", () => {
    expect(recoveryColor(99)).toBe(COLORS.recGreen);
    expect(recoveryColor(67)).toBe(COLORS.recGreen);
    expect(recoveryColor(66)).toBe(COLORS.recYellow);
    expect(recoveryColor(34)).toBe(COLORS.recYellow);
    expect(recoveryColor(33)).toBe(COLORS.recRed);
    expect(recoveryColor(0)).toBe(COLORS.recRed);
  });

  it("COLORS stay in sync with globals.css", () => {
    const css = fs.readFileSync(
      path.resolve(__dirname, "../../src/app/globals.css"),
      "utf-8",
    );

    // Pin each JS constant to its CSS counterpart. Both sides must match.
    const pairs: Array<[string, string]> = [
      [COLORS.recGreen, "#16ec06"],
      [COLORS.recYellow, "#ffde00"],
      [COLORS.recRed, "#ff0026"],
      [COLORS.recBlue, "#67aee6"],
      [COLORS.strain, "#0093e7"],
      [COLORS.sleep, "#7ba1bb"],
      [COLORS.teal, "#00f19f"],
      [COLORS.bgTop, "#283339"],
      [COLORS.bgBottom, "#101518"],
      [COLORS.card, "#1a2227"],
      [COLORS.cardAlt, "#1f2a30"],
    ];

    for (const [jsValue, cssValue] of pairs) {
      expect(jsValue.toLowerCase()).toBe(cssValue);
      expect(css).toContain(cssValue);
    }
  });
});
