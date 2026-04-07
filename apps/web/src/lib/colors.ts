/**
 * Whoop palette constants — for ECharts options and any JS that needs
 * a hex code instead of a CSS variable. Must stay in sync with globals.css.
 * A unit test asserts they don't drift.
 */
export const COLORS = {
  bgTop: "#283339",
  bgBottom: "#101518",

  card: "#1A2227",
  cardAlt: "#1F2A30",

  textPrimary: "#FFFFFF",
  text2: "rgba(255,255,255,0.72)",
  text3: "rgba(255,255,255,0.48)",

  recGreen: "#16EC06",
  recYellow: "#FFDE00",
  recRed: "#FF0026",
  recBlue: "#67AEE6",

  strain: "#0093E7",
  sleep: "#7BA1BB",
  teal: "#00F19F",
} as const;

export function recoveryColor(pct: number): string {
  if (pct >= 67) return COLORS.recGreen;
  if (pct >= 34) return COLORS.recYellow;
  return COLORS.recRed;
}
