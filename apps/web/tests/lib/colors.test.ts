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
    expect(css).toContain("#16ec06"); // rec-green
    expect(css).toContain("#ffde00"); // rec-yellow
    expect(css).toContain("#ff0026"); // rec-red
    expect(css).toContain("#0093e7"); // strain
    expect(css).toContain("#7ba1bb"); // sleep
    expect(css).toContain("#00f19f"); // teal
  });
});
