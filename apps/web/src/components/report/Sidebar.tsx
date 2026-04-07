"use client";

import { clsx } from "clsx";

import type { WhoopReport } from "@/lib/types";

export type SectionKey =
  | "overview"
  | "recovery"
  | "sleep"
  | "strain"
  | "trends"
  | "workouts"
  | "journal";

type Props = {
  active: SectionKey;
  onChange: (key: SectionKey) => void;
  report: WhoopReport;
};

const ALL_SECTIONS: { key: SectionKey; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "recovery", label: "Recovery" },
  { key: "sleep", label: "Sleep" },
  { key: "strain", label: "Strain" },
  { key: "trends", label: "Trends" },
  { key: "workouts", label: "Workouts" },
  { key: "journal", label: "Journal" },
];

export function Sidebar({ active, onChange, report }: Props) {
  const sections = ALL_SECTIONS.filter((s) => {
    if (s.key === "workouts") return report.workouts !== null;
    if (s.key === "journal") return report.journal !== null;
    return true;
  });
  return (
    <aside className="flex flex-col border-r border-white/5 bg-black/20 p-5">
      <div className="mb-8 font-mono text-base font-extrabold tracking-[0.18em]">
        WHOOP·LENS
      </div>
      <nav>
        <ul className="space-y-1">
          {sections.map((s) => (
            <li key={s.key}>
              <button
                type="button"
                onClick={() => onChange(s.key)}
                className={clsx(
                  "w-full rounded-md px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-[0.1em] transition",
                  s.key === active
                    ? "bg-white/5 text-text-primary"
                    : "text-text-2 hover:text-text-primary",
                )}
              >
                {s.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
