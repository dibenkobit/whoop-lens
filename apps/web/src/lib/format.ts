/**
 * Number and duration formatters for the UI.
 * Pure functions — no side effects, no locale dependencies.
 */

export function formatPct(value: number, digits = 0): string {
  return `${value.toFixed(digits)}%`;
}

export function formatHours(minutes: number): string {
  const total = Math.round(minutes);
  const h = Math.floor(total / 60);
  const m = total % 60;
  return `${h}h ${m}m`;
}

export function formatHoursDecimal(hours: number, digits = 1): string {
  return `${hours.toFixed(digits)}h`;
}

export function formatBpm(value: number): string {
  return `${Math.round(value)} bpm`;
}

export function formatMs(value: number): string {
  return `${Math.round(value)} ms`;
}

export function formatDelta(value: number, unit = "pp"): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${Math.round(value)} ${unit}`;
}

export function formatDate(iso: string): string {
  // "2025-01-15" → "Jan 15"
  const [year, month, day] = iso.split("-").map(Number);
  if (
    year === undefined ||
    month === undefined ||
    day === undefined ||
    Number.isNaN(year) ||
    Number.isNaN(month) ||
    Number.isNaN(day)
  ) {
    return iso;
  }
  const date = new Date(year, month - 1, day);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function formatDateLong(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  if (
    year === undefined ||
    month === undefined ||
    day === undefined ||
    Number.isNaN(year) ||
    Number.isNaN(month) ||
    Number.isNaN(day)
  ) {
    return iso;
  }
  const date = new Date(year, month - 1, day);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatPeriod(start: string, end: string): string {
  return `${formatDateLong(start)} — ${formatDateLong(end)}`;
}

export function clockFrom24h(h: number): string {
  // Accepts a "day-aligned" hour (0-35.99) and returns HH:MM
  const wrapped = ((h % 24) + 24) % 24;
  const hh = Math.floor(wrapped);
  const mm = Math.round((wrapped - hh) * 60);
  if (mm === 60) {
    return `${String((hh + 1) % 24).padStart(2, "0")}:00`;
  }
  return `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}`;
}
