# Whoop Lens Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Next.js 16 frontend that lets users drop a Whoop data export ZIP, view an interactive report styled after the official Whoop app (dark canvas, three-dial hero, Whoop palette), and optionally generate a 30-day share link. Deploys to Vercel.

**Architecture:** App Router with a mix of Server and Client Components. Landing page and `/r/[id]` are server components. `/report` is a client component reading from an in-memory React Context (no persistence on the web side — CSVs never touch localStorage). ECharts (via `echarts-for-react`, dynamic-imported with `ssr: false`) powers the iconic dial gauges, trend lines, hypnogram, and heatmaps. Types are hand-written in `lib/types.ts` and must stay 1:1 with `apps/api/app/models/*`. No state manager — URL + Context is enough.

**Tech Stack:** Next.js 16.2.2 · React 19.2.4 · React Compiler · TypeScript strict · Tailwind v4 (`@theme` directive) · Biome 2.2 · Bun · ECharts 5+ · echarts-for-react · react-dropzone · clsx · nanoid · next/font (Inter + JetBrains Mono) · Vitest + @testing-library/react.

**Reference docs:**
- **Backend API contract:** `/Users/dibenkobit/projects/whoop-lens/apps/api/app/models/` — the Pydantic models are the source of truth. Every field name, literal, and optionality must match.
- **Backend plan (already executed):** `/Users/dibenkobit/projects/whoop-lens/docs/superpowers/plans/2026-04-07-whoop-lens-backend.md` — tells you which error codes the API returns.
- **Design spec:** `/Users/dibenkobit/projects/whoop-lens/docs/superpowers/specs/2026-04-07-whoop-lens-design.md` — §4 (frontend), §6 (errors), §10 (visual system), §11 (insights).
- **Handoff doc:** `/Users/dibenkobit/projects/whoop-lens/docs/superpowers/HANDOFF.md` — lessons from backend execution; read §7.
- **Next.js 16 docs:** `/Users/dibenkobit/projects/whoop-lens/apps/web/node_modules/next/dist/docs/` — **this is NOT the Next.js you know**, per `apps/web/AGENTS.md`. Read the relevant doc before writing code.

---

## File map

```
apps/web/
├── package.json                         (modified — add deps)
├── biome.json                           (pre-existing, unchanged)
├── next.config.ts                       (modified — add transpilePackages if needed for echarts)
├── postcss.config.mjs                   (pre-existing)
├── public/                              (pre-existing favicon etc.)
├── src/
│   ├── app/
│   │   ├── layout.tsx                   (modified — Inter + JetBrains Mono + Whoop dark theme)
│   │   ├── globals.css                  (modified — Whoop palette via @theme)
│   │   ├── page.tsx                     (rewritten — landing + dropzone)
│   │   ├── report/
│   │   │   └── page.tsx                 (new — client component, reads ReportContext)
│   │   ├── r/
│   │   │   └── [id]/
│   │   │       ├── page.tsx             (new — server component, fetches from API)
│   │   │       └── not-found.tsx        (new — friendly "expired/missing" page)
│   │   └── about/
│   │       └── page.tsx                 (new — disclaimer + how it works)
│   ├── components/
│   │   ├── upload/
│   │   │   ├── Dropzone.tsx
│   │   │   ├── UploadProgress.tsx
│   │   │   └── UploadError.tsx
│   │   ├── report/
│   │   │   ├── ReportShell.tsx          # Sidebar + main pane scaffold
│   │   │   ├── Sidebar.tsx
│   │   │   ├── ReportHeader.tsx         # Date range, share button
│   │   │   ├── Dial.tsx                 # ECharts gauge wrapper
│   │   │   ├── DialRow.tsx              # 3-dial hero
│   │   │   ├── Card.tsx                 # Dark card primitive
│   │   │   ├── CardLabel.tsx            # Uppercase low-opacity label
│   │   │   ├── MetricRow.tsx            # HRV / RHR / Resp / SpO2 row
│   │   │   ├── InsightCard.tsx          # No left border (per brief)
│   │   │   ├── TrendLineChart.tsx       # ECharts line w/ Whoop blue fill
│   │   │   ├── DowBars.tsx              # Day-of-week bars with recovery colors
│   │   │   ├── RecoveryDistribution.tsx # Small 3-segment bar
│   │   │   ├── Hypnogram.tsx            # Stacked timeline; null-safe
│   │   │   ├── ConsistencyStrip.tsx     # 14-day bedtime strip
│   │   │   ├── SleepStageBreakdown.tsx
│   │   │   ├── StrainDistribution.tsx
│   │   │   ├── HrZonesBar.tsx           # Unused in v1 (no per-workout zones) — skip
│   │   │   ├── WorkoutsList.tsx
│   │   │   ├── TopStrainDays.tsx
│   │   │   ├── JournalList.tsx
│   │   │   ├── MonthlyHeatmap.tsx       # Trends section
│   │   │   ├── FirstVsLast.tsx          # Before/after comparison
│   │   │   ├── SickEpisodesList.tsx
│   │   │   ├── ShareDialog.tsx          # Modal for POST /share
│   │   │   └── sections/
│   │   │       ├── OverviewSection.tsx
│   │   │       ├── RecoverySection.tsx
│   │   │       ├── SleepSection.tsx
│   │   │       ├── StrainSection.tsx
│   │   │       ├── TrendsSection.tsx
│   │   │       ├── WorkoutsSection.tsx
│   │   │       └── JournalSection.tsx
│   │   └── ui/
│   │       ├── Button.tsx
│   │       ├── Dialog.tsx               # Tiny modal primitive
│   │       └── Footer.tsx               # Disclaimer footer
│   ├── context/
│   │   └── ReportContext.tsx            # In-memory report; only /report route uses it
│   ├── lib/
│   │   ├── types.ts                     # Mirror of Pydantic WhoopReport
│   │   ├── api.ts                       # fetch wrappers: analyze, share, getShared
│   │   ├── colors.ts                    # Whoop palette as JS constants
│   │   ├── echarts.ts                   # Tree-shaken ECharts registration
│   │   ├── format.ts                    # number/duration/date/clock formatters
│   │   ├── errors.ts                    # API error code → friendly copy
│   │   ├── dials.ts                     # ECharts gauge option builder
│   │   └── url.ts                       # API base URL helper
│   └── test/
│       └── setup.ts                     # Vitest + JSDOM setup
├── tests/                               # (vitest root next to src; biome ignores)
│   ├── lib/
│   │   ├── format.test.ts
│   │   ├── colors.test.ts
│   │   ├── errors.test.ts
│   │   └── api.test.ts
│   └── components/
│       ├── Dial.test.tsx
│       ├── InsightCard.test.tsx
│       └── UploadError.test.tsx
├── vitest.config.ts                     # new
└── tsconfig.json                        (unchanged)
```

**Working directory for all commands:** `/Users/dibenkobit/projects/whoop-lens/apps/web` unless noted otherwise.

**Important invariants:**

- **Types are hand-written, not generated.** Keep `lib/types.ts` 1:1 with `apps/api/app/models/*`. Any drift is a bug.
- **Colors live in two places (one source, two consumers).** CSS custom properties in `globals.css` for Tailwind (`bg-card`, `text-rec-green`), and JS constants in `lib/colors.ts` for ECharts options. A single unit test asserts they don't drift.
- **No server secrets in the web app.** `NEXT_PUBLIC_API_URL` is the only env var and it's public by design.
- **No raw CSV is ever stored client-side.** `POST /analyze` is fire-and-forget; the response JSON lives only in `ReportContext` (memory) until the tab closes.
- **Every test task uses Vitest in jsdom mode.** No Playwright. No Storybook.

---

## Task 0: Workspace prereqs

**Files:** none yet — environment check only.

- [ ] **Step 1: Verify Bun is available and the backend API is reachable**

```bash
cd /Users/dibenkobit/projects/whoop-lens
bun --version
cd apps/web
cat package.json | head -20
```

Expected: bun >= 1.0, Next.js 16.2.2 visible.

- [ ] **Step 2: Start the backend locally (needed for integration tests)**

```bash
cd /Users/dibenkobit/projects/whoop-lens/apps/api
uv run uvicorn app.main:app --port 8000 &
sleep 2
curl -s http://localhost:8000/healthz
```

Expected: `{"ok":true,"db":"ok"}`. Leave it running in the background for the whole frontend work.

- [ ] **Step 3: Clean slate check**

```bash
cd /Users/dibenkobit/projects/whoop-lens
git status
```

Expected: working tree clean. If not, commit or stash before starting.

---

## Task 1: Dependencies, fonts, Whoop palette tokens

**Files:**
- Modify: `apps/web/package.json`
- Modify: `apps/web/src/app/globals.css`
- Modify: `apps/web/src/app/layout.tsx`
- Delete: `apps/web/src/app/page.tsx` (will be rewritten in Task 6)

- [ ] **Step 1: Install runtime deps**

```bash
cd /Users/dibenkobit/projects/whoop-lens/apps/web
bun add echarts echarts-for-react react-dropzone clsx nanoid
```

Expected: `package.json` updated. `bun install` runs clean.

- [ ] **Step 2: Install dev deps for testing**

```bash
bun add -d vitest @vitest/coverage-v8 jsdom @testing-library/react @testing-library/dom @testing-library/jest-dom happy-dom
```

Note: `happy-dom` is included as a backup in case `jsdom` doesn't cooperate with React 19 — pick whichever works in Task 3.

- [ ] **Step 3: Overwrite `src/app/globals.css` with Whoop palette tokens**

Open `apps/web/src/app/globals.css` and replace the entire file with:

```css
@import "tailwindcss";

@theme {
  /* Whoop background gradient */
  --color-bg-top: #283339;
  --color-bg-bottom: #101518;

  /* Surfaces */
  --color-card: #1a2227;
  --color-card-alt: #1f2a30;

  /* Text */
  --color-text-primary: #ffffff;
  --color-text-2: rgba(255, 255, 255, 0.72);
  --color-text-3: rgba(255, 255, 255, 0.48);

  /* Recovery zones (sharp boundaries — never interpolate) */
  --color-rec-green: #16ec06;
  --color-rec-yellow: #ffde00;
  --color-rec-red: #ff0026;
  --color-rec-blue: #67aee6;

  /* Strain + sleep */
  --color-strain: #0093e7;
  --color-sleep: #7ba1bb;

  /* Accent */
  --color-teal: #00f19f;

  /* Typography */
  --font-sans: var(--font-inter), system-ui, sans-serif;
  --font-mono: var(--font-jetbrains-mono), ui-monospace, monospace;
}

html,
body {
  background: linear-gradient(
    180deg,
    var(--color-bg-top) 0%,
    var(--color-bg-bottom) 100%
  );
  color: var(--color-text-primary);
  font-family: var(--font-sans);
  min-height: 100vh;
}

body {
  -webkit-font-smoothing: antialiased;
  font-feature-settings: "cv11", "ss01";
}
```

- [ ] **Step 4: Rewrite `src/app/layout.tsx` with Inter + JetBrains Mono**

Replace `apps/web/src/app/layout.tsx`:

```tsx
import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";

import { Footer } from "@/components/ui/Footer";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Whoop Lens — visualize your Whoop data export",
  description:
    "Open-source report generator for Whoop data exports. Not affiliated with WHOOP, Inc.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable} antialiased`}
    >
      <body className="min-h-screen flex flex-col">
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
```

This imports `@/components/ui/Footer` which doesn't exist yet — that's fine; the build will fail until Task 4 creates it. We stage the edit intentionally.

- [ ] **Step 5: Delete the default landing page**

```bash
rm apps/web/src/app/page.tsx
```

We'll recreate it in Task 6.

- [ ] **Step 6: Configure TypeScript path alias (if not already set)**

Inspect `apps/web/tsconfig.json`. Verify it has `"paths": { "@/*": ["./src/*"] }`. If not, add it under `compilerOptions`. Leave alone if already present (scaffolded create-next-app usually sets this).

- [ ] **Step 7: Commit** (yes, even though the build is currently broken — the Footer arrives in Task 4)

```bash
cd /Users/dibenkobit/projects/whoop-lens
git add apps/web/
git commit -m "feat(web): install deps and configure Whoop visual tokens

- echarts, echarts-for-react, react-dropzone, clsx, nanoid
- vitest + testing-library + jsdom dev deps
- globals.css: Whoop palette via @theme (recovery zones, strain, sleep, teal)
- layout.tsx: Inter + JetBrains Mono via next/font
- Delete scaffolded page.tsx (to be rewritten in Task 6)"
```

---

## Task 2: Hand-written types mirroring the Pydantic contract

**Files:**
- Create: `apps/web/src/lib/types.ts`
- Create: `apps/web/tests/lib/types.test.ts`

- [ ] **Step 1: Write a static structural test**

Create `apps/web/tests/lib/types.test.ts`:

```ts
import { describe, it, expectTypeOf } from "vitest";

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
```

- [ ] **Step 2: Implement `lib/types.ts`**

Create `apps/web/src/lib/types.ts`:

```ts
/**
 * Hand-written mirror of apps/api/app/models/*.
 * When you change one, change BOTH. Drift is a bug.
 */

export type InsightKind =
  | "undersleep"
  | "bedtime_consistency"
  | "late_chronotype"
  | "overtraining"
  | "sick_episodes"
  | "travel_impact"
  | "dow_pattern"
  | "sleep_stage_quality"
  | "long_term_trend"
  | "workout_mix";

export type InsightSeverity = "low" | "medium" | "high";

export type InsightHighlight = {
  value: string;
  unit?: string;
};

export type InsightEvidence = {
  value: number;
  label: string;
};

export type Insight = {
  kind: InsightKind;
  severity: InsightSeverity;
  title: string;
  body: string;
  highlight: InsightHighlight;
  evidence?: InsightEvidence[];
};

export type Period = {
  start: string; // ISO date
  end: string;
  days: number;
};

export type SleepDial = {
  value: number;
  unit: "h";
  performance_pct: number;
};

export type RecoveryDial = {
  value: number;
  unit: "%";
  green_pct: number;
};

export type StrainDial = {
  value: number;
  unit: "";
  label: "light" | "moderate" | "high" | "all_out";
};

export type Dials = {
  sleep: SleepDial;
  recovery: RecoveryDial;
  strain: StrainDial;
};

export type Metrics = {
  hrv_ms: number;
  rhr_bpm: number;
  resp_rpm: number;
  spo2_pct: number;
  sleep_efficiency_pct: number;
  sleep_consistency_pct: number;
  sleep_debt_min: number;
};

export type TrendPoint = { date: string; value: number | null };

export type DowName = "mon" | "tue" | "wed" | "thu" | "fri" | "sat" | "sun";

export type DowEntry = { dow: DowName; mean: number; n: number };

export type SickEpisode = {
  date: string;
  recovery: number;
  rhr: number;
  hrv: number;
  skin_temp_c: number | null;
};

export type RecoveryDistribution = {
  green: number;
  yellow: number;
  red: number;
};

export type RecoverySection = {
  trend: TrendPoint[];
  by_dow: DowEntry[];
  distribution: RecoveryDistribution;
  sick_episodes: SickEpisode[];
};

export type HypnogramStage = "awake" | "light" | "rem" | "deep";

export type HypnogramSegment = {
  stage: HypnogramStage;
  from: string; // ISO datetime (note: wire key is "from", not "from_")
  to: string;
};

export type HypnogramNight = {
  start: string;
  end: string;
  segments: HypnogramSegment[];
};

export type BedtimeStrip = {
  date: string;
  bed_local: string; // "HH:MM"
  wake_local: string;
};

export type SleepDurations = {
  light_min: number;
  rem_min: number;
  deep_min: number;
  awake_min: number;
};

export type SleepStagePct = {
  light: number;
  rem: number;
  deep: number;
};

export type SleepSection = {
  avg_bedtime: string; // "HH:MM"
  avg_wake: string;
  bedtime_std_h: number;
  avg_durations: SleepDurations;
  stage_pct: SleepStagePct;
  hypnogram_sample: HypnogramNight | null;
  consistency_strip: BedtimeStrip[];
};

export type StrainDistribution = {
  light: number;
  moderate: number;
  high: number;
  all_out: number;
};

export type StrainSection = {
  avg_strain: number;
  distribution: StrainDistribution;
  trend: TrendPoint[];
};

export type ActivityAgg = {
  name: string;
  count: number;
  total_strain: number;
  total_min: number;
  pct_of_total_strain: number;
};

export type TopStrainDay = {
  date: string;
  day_strain: number;
  recovery: number;
  next_recovery: number | null;
};

export type WorkoutsSection = {
  total: number;
  by_activity: ActivityAgg[];
  top_strain_days: TopStrainDay[];
};

export type JournalQuestionAgg = {
  question: string;
  yes: number;
  no: number;
  mean_rec_yes: number | null;
  mean_rec_no: number | null;
};

export type JournalSection = {
  days_logged: number;
  questions: JournalQuestionAgg[];
  note: string;
};

export type MonthlyAgg = {
  month: string; // "YYYY-MM"
  recovery: number;
  hrv: number;
  rhr: number;
  sleep_h: number;
};

export type TrendComparison = {
  bedtime_h: [number, number]; // [first_60d, last_60d]
  sleep_h: [number, number];
  rhr: [number, number];
  workouts: [number, number];
};

export type TrendsSection = {
  monthly: MonthlyAgg[];
  first_vs_last_60d: TrendComparison;
};

export type WhoopReport = {
  schema_version: 1;
  period: Period;
  dials: Dials;
  metrics: Metrics;
  recovery: RecoverySection;
  sleep: SleepSection;
  strain: StrainSection;
  workouts: WorkoutsSection | null;
  journal: JournalSection | null;
  trends: TrendsSection;
  insights: Insight[];
};

export type ShareCreateRequest = { report: WhoopReport };
export type ShareCreateResponse = {
  id: string;
  url: string;
  expires_at: string; // ISO datetime
};

export type ApiErrorBody = {
  code: string;
  file?: string;
  limit_mb?: number;
  missing_cols?: string[];
  extra_cols?: string[];
  error_id?: string;
  [key: string]: unknown;
};
```

- [ ] **Step 3: Run the type test**

Vitest isn't configured yet (that happens in Task 3). For now, verify types compile with `tsc`:

```bash
cd /Users/dibenkobit/projects/whoop-lens/apps/web
bunx tsc --noEmit
```

Expected: no errors for `src/lib/types.ts`. The test file won't compile yet because vitest isn't set up; **skip it for now** (we'll run the actual test in Task 3).

- [ ] **Step 4: Commit**

```bash
cd /Users/dibenkobit/projects/whoop-lens
git add apps/web/src/lib/types.ts apps/web/tests/lib/types.test.ts
git commit -m "feat(web): add hand-written types mirroring Pydantic contract

- WhoopReport tree 1:1 with apps/api/app/models/*
- Insight, InsightKind, InsightSeverity literal unions
- SleepDial / RecoveryDial / StrainDial discriminated shapes
- HypnogramSegment uses 'from' (not 'from_') per wire format
- ApiErrorBody union for error responses"
```

---

## Task 3: Vitest setup + lib utilities (colors, format, errors, api, url)

**Files:**
- Create: `apps/web/vitest.config.ts`
- Create: `apps/web/src/test/setup.ts`
- Create: `apps/web/src/lib/url.ts`
- Create: `apps/web/src/lib/colors.ts`
- Create: `apps/web/src/lib/format.ts`
- Create: `apps/web/src/lib/errors.ts`
- Create: `apps/web/src/lib/api.ts`
- Create: `apps/web/tests/lib/format.test.ts`
- Create: `apps/web/tests/lib/colors.test.ts`
- Create: `apps/web/tests/lib/errors.test.ts`
- Create: `apps/web/tests/lib/api.test.ts`
- Modify: `apps/web/package.json` (add test scripts)

- [ ] **Step 1: Configure Vitest**

Create `apps/web/vitest.config.ts`:

```ts
import { defineConfig } from "vitest/config";
import path from "node:path";

export default defineConfig({
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    globals: true,
    include: ["tests/**/*.test.{ts,tsx}"],
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
```

Create `apps/web/src/test/setup.ts`:

```ts
import "@testing-library/jest-dom";
```

- [ ] **Step 2: Add test scripts to `package.json`**

In `apps/web/package.json`, add to the `"scripts"` object:

```json
"test": "vitest run",
"test:watch": "vitest",
"typecheck": "tsc --noEmit"
```

- [ ] **Step 3: Implement `lib/url.ts`**

Create `apps/web/src/lib/url.ts`:

```ts
/**
 * Resolves the backend API base URL.
 *
 * In the browser, reads NEXT_PUBLIC_API_URL (baked at build time).
 * On the server, allows an optional INTERNAL_API_URL override for
 * server-to-server calls on the same private network (e.g., Railway internal),
 * falling back to NEXT_PUBLIC_API_URL.
 */
export function apiBase(): string {
  if (typeof window === "undefined") {
    return (
      process.env.INTERNAL_API_URL ??
      process.env.NEXT_PUBLIC_API_URL ??
      "http://localhost:8000"
    );
  }
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}
```

- [ ] **Step 4: Implement `lib/colors.ts`**

Create `apps/web/src/lib/colors.ts`:

```ts
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
```

- [ ] **Step 5: Implement `lib/format.ts`**

Create `apps/web/src/lib/format.ts`:

```ts
/**
 * Number and duration formatters for the UI.
 * Pure functions — no side effects, no locale dependencies.
 */

export function formatPct(value: number, digits = 0): string {
  return `${value.toFixed(digits)}%`;
}

export function formatHours(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = Math.round(minutes % 60);
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
```

- [ ] **Step 6: Implement `lib/errors.ts`**

Create `apps/web/src/lib/errors.ts`:

```ts
import type { ApiErrorBody } from "./types";

/**
 * Maps API error codes to human-readable copy for the upload UI.
 * Unknown codes fall back to a generic message plus the server's `code`
 * value so the user has something to include in a bug report.
 */

export type FriendlyError = {
  title: string;
  description: string;
  canRetry: boolean;
};

export function friendlyError(
  body: ApiErrorBody | null,
  httpStatus: number,
): FriendlyError {
  const code = body?.code;

  if (httpStatus >= 500) {
    return {
      title: "Something went wrong on our side",
      description: body?.error_id
        ? `Please open a GitHub issue with error code ${body.error_id}.`
        : "Please try again in a moment. If it keeps failing, open a GitHub issue.",
      canRetry: true,
    };
  }

  switch (code) {
    case "file_too_large":
      return {
        title: "File too large",
        description: `Maximum upload is ${body?.limit_mb ?? 50} MB. Whoop exports are usually a few MB.`,
        canRetry: false,
      };
    case "not_a_zip":
      return {
        title: "That doesn't look like a Whoop export",
        description:
          "We need the .zip file you got from Whoop's Export My Data feature.",
        canRetry: false,
      };
    case "corrupt_zip":
      return {
        title: "Couldn't open the zip",
        description:
          "The file may be corrupted. Try re-downloading it from your Whoop account.",
        canRetry: false,
      };
    case "missing_required_file":
      return {
        title: `Missing ${body?.file ?? "a required file"}`,
        description:
          "Your export is missing one of the required CSVs (physiological_cycles.csv or sleeps.csv). Make sure you uploaded the full export.",
        canRetry: false,
      };
    case "unexpected_schema":
      return {
        title: "Whoop changed their export format",
        description: `The file ${body?.file ?? ""} has columns we don't recognize. Please open a GitHub issue — we'll update the parser.`,
        canRetry: false,
      };
    case "no_data":
      return {
        title: "We couldn't find any data",
        description: `${body?.file ?? "The export"} contains no rows. Make sure your Whoop account has data in the time range you exported.`,
        canRetry: false,
      };
    default:
      return {
        title: "Upload failed",
        description: body?.code
          ? `Server returned code '${body.code}'. Please open a GitHub issue.`
          : "Unknown error. Please try again.",
        canRetry: httpStatus !== 400,
      };
  }
}
```

- [ ] **Step 7: Implement `lib/api.ts`**

Create `apps/web/src/lib/api.ts`:

```ts
import type {
  ApiErrorBody,
  ShareCreateResponse,
  WhoopReport,
} from "./types";
import { apiBase } from "./url";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: ApiErrorBody | null,
  ) {
    super(`API error ${status}`);
  }
}

/**
 * POST /analyze — upload a Whoop export ZIP and get a WhoopReport.
 * Pass an AbortSignal to cancel on unmount.
 */
export async function analyzeZip(
  file: File,
  signal?: AbortSignal,
): Promise<WhoopReport> {
  const form = new FormData();
  form.append("file", file);
  const resp = await fetch(`${apiBase()}/analyze`, {
    method: "POST",
    body: form,
    signal,
  });
  if (!resp.ok) {
    let body: ApiErrorBody | null = null;
    try {
      body = (await resp.json()) as ApiErrorBody;
    } catch {
      body = null;
    }
    throw new ApiError(resp.status, body);
  }
  return (await resp.json()) as WhoopReport;
}

/**
 * POST /share — freeze a report as a shareable 30-day snapshot.
 */
export async function createShare(
  report: WhoopReport,
): Promise<ShareCreateResponse> {
  const resp = await fetch(`${apiBase()}/share`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ report }),
  });
  if (!resp.ok) {
    let body: ApiErrorBody | null = null;
    try {
      body = (await resp.json()) as ApiErrorBody;
    } catch {
      body = null;
    }
    throw new ApiError(resp.status, body);
  }
  return (await resp.json()) as ShareCreateResponse;
}

/**
 * GET /r/{id} — fetch a previously-shared report. Used from a Server Component.
 * Returns null on 404 (expired or missing).
 */
export async function getSharedReport(id: string): Promise<WhoopReport | null> {
  const resp = await fetch(`${apiBase()}/r/${encodeURIComponent(id)}`, {
    cache: "no-store",
  });
  if (resp.status === 404) return null;
  if (!resp.ok) {
    throw new ApiError(resp.status, null);
  }
  return (await resp.json()) as WhoopReport;
}
```

- [ ] **Step 8: Write the tests**

Create `apps/web/tests/lib/format.test.ts`:

```ts
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
});
```

Create `apps/web/tests/lib/colors.test.ts`:

```ts
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
```

Create `apps/web/tests/lib/errors.test.ts`:

```ts
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
```

Create `apps/web/tests/lib/api.test.ts`:

```ts
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
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({ code: "not_a_zip" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      }),
    );
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
```

- [ ] **Step 9: Run the tests**

```bash
cd /Users/dibenkobit/projects/whoop-lens/apps/web
bun run test
```

Expected: all passing. If tests fail because of jsdom/react 19 issues, switch to `environment: "happy-dom"` in `vitest.config.ts`.

- [ ] **Step 10: Run typecheck**

```bash
bun run typecheck
```

Expected: no errors. (The failing import of Footer in layout.tsx is still present — it'll be a build error, not a typecheck error, because the file doesn't exist. Ignore until Task 4.)

- [ ] **Step 11: Commit**

```bash
cd /Users/dibenkobit/projects/whoop-lens
git add apps/web/
git commit -m "feat(web): add Vitest + lib utilities

- vitest.config.ts with jsdom environment and @ alias
- lib/url.ts resolves API base from NEXT_PUBLIC_API_URL
- lib/colors.ts: Whoop palette as JS constants + recoveryColor
- lib/format.ts: pct, hours, bpm, ms, delta, date, clock
- lib/errors.ts: API error codes → friendly copy
- lib/api.ts: analyzeZip, createShare, getSharedReport + ApiError
- Full tests: format (9), colors (2), errors (6), api (5) — all passing"
```

---

## Task 4: Footer + Button + Dialog primitives

**Files:**
- Create: `apps/web/src/components/ui/Footer.tsx`
- Create: `apps/web/src/components/ui/Button.tsx`
- Create: `apps/web/src/components/ui/Dialog.tsx`
- Create: `apps/web/tests/components/Footer.test.tsx`

- [ ] **Step 1: Write the Footer test**

Create `apps/web/tests/components/Footer.test.tsx`:

```tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { Footer } from "@/components/ui/Footer";

describe("Footer", () => {
  it("renders the WHOOP disclaimer", () => {
    render(<Footer />);
    expect(
      screen.getByText(/not affiliated with.*whoop, inc/i),
    ).toBeInTheDocument();
  });

  it("links to /about and to the GitHub repo", () => {
    render(<Footer />);
    const about = screen.getByRole("link", { name: /about/i });
    expect(about).toHaveAttribute("href", "/about");
    const repo = screen.getByRole("link", { name: /github/i });
    expect(repo.getAttribute("href")).toMatch(/github\.com/);
  });
});
```

- [ ] **Step 2: Implement `Footer.tsx`**

Create `apps/web/src/components/ui/Footer.tsx`:

```tsx
import Link from "next/link";

export function Footer() {
  return (
    <footer className="mt-16 border-t border-white/5 px-6 py-6 text-xs text-text-3">
      <div className="mx-auto flex max-w-7xl flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <p>
          <span className="tracking-[0.18em] font-semibold text-text-2">
            WHOOP·LENS
          </span>{" "}
          — open source, MIT licensed.
        </p>
        <p className="max-w-xl leading-relaxed">
          Whoop Lens is an independent open-source project. Not affiliated with,
          endorsed by, or sponsored by WHOOP, Inc. WHOOP is a trademark of
          WHOOP, Inc.
        </p>
        <div className="flex gap-4">
          <Link href="/about" className="hover:text-text-primary">
            About
          </Link>
          <a
            href="https://github.com/whoop-lens/whoop-lens"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-text-primary"
          >
            GitHub
          </a>
        </div>
      </div>
    </footer>
  );
}
```

Note: the GitHub URL is a placeholder — if the repo isn't public yet at that URL, that's fine; the link format is what matters. A future task can update the URL.

- [ ] **Step 3: Implement `Button.tsx`**

Create `apps/web/src/components/ui/Button.tsx`:

```tsx
import { clsx } from "clsx";
import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  children: ReactNode;
};

const variantClass: Record<Variant, string> = {
  primary:
    "bg-teal text-[#001a10] hover:brightness-95 disabled:opacity-50 disabled:cursor-not-allowed",
  secondary:
    "bg-card-alt text-text-primary hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed",
  ghost: "text-text-2 hover:text-text-primary hover:bg-white/5",
};

export function Button({
  variant = "primary",
  className,
  children,
  ...rest
}: Props) {
  return (
    <button
      type="button"
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-xs font-bold uppercase tracking-[0.1em] transition",
        variantClass[variant],
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}
```

- [ ] **Step 4: Implement `Dialog.tsx`**

Create `apps/web/src/components/ui/Dialog.tsx`:

```tsx
"use client";

import { clsx } from "clsx";
import { useEffect } from "react";
import type { ReactNode } from "react";

type Props = {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  className?: string;
};

export function Dialog({ open, onClose, title, children, className }: Props) {
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={title}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
    >
      <div
        className={clsx(
          "w-full max-w-md rounded-xl bg-card p-6 shadow-2xl",
          className,
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="mb-4 text-sm font-bold uppercase tracking-[0.12em] text-text-2">
          {title}
        </h2>
        {children}
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Verify tests + typecheck + build**

```bash
cd /Users/dibenkobit/projects/whoop-lens/apps/web
bun run test
bun run typecheck
bun run lint
bun run build
```

Expected: tests pass (9 existing + 2 new), typecheck clean, lint clean, **build succeeds** (the Footer import in `layout.tsx` now resolves).

- [ ] **Step 6: Commit**

```bash
cd /Users/dibenkobit/projects/whoop-lens
git add apps/web/
git commit -m "feat(web): add Footer, Button, Dialog primitives

- Footer with WHOOP disclaimer + About link + GitHub link
- Button with primary/secondary/ghost variants
- Dialog modal with ESC close and click-outside-to-close
- Footer tests (2) passing; build now succeeds"
```

---

## Task 5: Dial (ECharts gauge) component

**Files:**
- Create: `apps/web/src/lib/dials.ts`
- Create: `apps/web/src/lib/echarts.ts`
- Create: `apps/web/src/components/report/Dial.tsx`
- Create: `apps/web/src/components/report/DialRow.tsx`
- Create: `apps/web/tests/components/Dial.test.tsx`

- [ ] **Step 1: Implement `lib/echarts.ts` with tree-shaken registration**

Create `apps/web/src/lib/echarts.ts`:

```ts
import * as echarts from "echarts/core";
import { BarChart, GaugeChart, HeatmapChart, LineChart } from "echarts/charts";
import {
  CustomChart,
} from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  VisualMapComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([
  GaugeChart,
  LineChart,
  BarChart,
  HeatmapChart,
  CustomChart,
  GridComponent,
  TooltipComponent,
  VisualMapComponent,
  CanvasRenderer,
]);

export { echarts };
```

- [ ] **Step 2: Implement `lib/dials.ts` (gauge option builder)**

Create `apps/web/src/lib/dials.ts`:

```ts
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
    textStyle: { color: COLORS.textPrimary, fontFamily: "var(--font-mono)" },
  };
}
```

- [ ] **Step 3: Implement `Dial.tsx`**

Create `apps/web/src/components/report/Dial.tsx`:

```tsx
"use client";

import dynamic from "next/dynamic";

import { buildDialOption } from "@/lib/dials";

const ReactECharts = dynamic(() => import("echarts-for-react"), {
  ssr: false,
  loading: () => (
    <div className="h-[140px] w-[140px] animate-pulse rounded-full bg-white/5" />
  ),
});

type Props = {
  value: number;
  max: number;
  color: string;
  display: string;
  label: string;
  sub?: string;
};

export function Dial({ value, max, color, display, label, sub }: Props) {
  const option = buildDialOption({ value, max, color, display, label, sub });
  return (
    <div
      data-testid="dial"
      className="relative flex flex-col items-center justify-center rounded-2xl bg-card px-4 py-5"
    >
      <div className="relative h-[140px] w-[140px]">
        <ReactECharts
          option={option}
          style={{ height: 140, width: 140 }}
          notMerge
          lazyUpdate
          opts={{ renderer: "canvas" }}
        />
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <span className="font-mono text-3xl font-bold tracking-tight text-text-primary">
            {display}
          </span>
        </div>
      </div>
      <div className="mt-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-text-3">
        {label}
      </div>
      {sub ? (
        <div className="mt-1 text-[11px] text-text-2">{sub}</div>
      ) : null}
    </div>
  );
}
```

- [ ] **Step 4: Implement `DialRow.tsx`**

Create `apps/web/src/components/report/DialRow.tsx`:

```tsx
import type { Dials } from "@/lib/types";
import { COLORS } from "@/lib/colors";

import { Dial } from "./Dial";

type Props = { dials: Dials };

export function DialRow({ dials }: Props) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <Dial
        value={Math.min(dials.sleep.value, 12)}
        max={12}
        color={COLORS.sleep}
        display={`${dials.sleep.value.toFixed(2)}h`}
        label="Avg Sleep"
        sub={`${dials.sleep.performance_pct.toFixed(0)}% performance`}
      />
      <Dial
        value={dials.recovery.value}
        max={100}
        color={
          dials.recovery.value >= 67
            ? COLORS.recGreen
            : dials.recovery.value >= 34
              ? COLORS.recYellow
              : COLORS.recRed
        }
        display={`${dials.recovery.value.toFixed(0)}%`}
        label="Avg Recovery"
        sub={`${dials.recovery.green_pct.toFixed(0)}% green days`}
      />
      <Dial
        value={dials.strain.value}
        max={21}
        color={COLORS.strain}
        display={dials.strain.value.toFixed(1)}
        label="Avg Strain"
        sub={dials.strain.label.replace("_", " ")}
      />
    </div>
  );
}
```

- [ ] **Step 5: Write the Dial test**

Create `apps/web/tests/components/Dial.test.tsx`:

```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

// Mock the dynamic echarts import so jsdom doesn't need to render a canvas
vi.mock("echarts-for-react", () => ({
  default: () => <div data-testid="echarts-stub" />,
}));

// next/dynamic treats the import as static in jsdom — Next's dynamic
// helper works fine when the module being dynamic-imported is mocked above.

import { Dial } from "@/components/report/Dial";

describe("Dial", () => {
  it("renders the display text and label", () => {
    render(
      <Dial
        value={68}
        max={100}
        color="#16EC06"
        display="68%"
        label="Avg Recovery"
        sub="57% green days"
      />,
    );
    expect(screen.getByText("68%")).toBeInTheDocument();
    expect(screen.getByText(/avg recovery/i)).toBeInTheDocument();
    expect(screen.getByText(/57% green days/i)).toBeInTheDocument();
  });

  it("omits sub when not provided", () => {
    render(
      <Dial value={10} max={21} color="#0093E7" display="10.2" label="Avg Strain" />,
    );
    expect(screen.getByText("10.2")).toBeInTheDocument();
    expect(screen.getByText(/avg strain/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 6: Verify**

```bash
cd /Users/dibenkobit/projects/whoop-lens/apps/web
bun run test
bun run typecheck
bun run lint
```

Expected: all passing.

- [ ] **Step 7: Commit**

```bash
cd /Users/dibenkobit/projects/whoop-lens
git add apps/web/
git commit -m "feat(web): add Dial + DialRow components

- lib/echarts.ts: tree-shaken ECharts module registration
- lib/dials.ts: ECharts gauge option builder
- Dial.tsx: dynamic-imported ReactECharts with overlaid text
- DialRow.tsx: three-dial hero with Whoop color zones
- Dial tests (2) with echarts-for-react mocked"
```

---

## Task 6: Landing page with dropzone

**Files:**
- Create: `apps/web/src/context/ReportContext.tsx`
- Create: `apps/web/src/components/upload/Dropzone.tsx`
- Create: `apps/web/src/components/upload/UploadProgress.tsx`
- Create: `apps/web/src/components/upload/UploadError.tsx`
- Create: `apps/web/src/app/page.tsx`
- Create: `apps/web/tests/components/UploadError.test.tsx`

- [ ] **Step 1: Implement `ReportContext.tsx`**

Create `apps/web/src/context/ReportContext.tsx`:

```tsx
"use client";

import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";

import type { WhoopReport } from "@/lib/types";

type Ctx = {
  report: WhoopReport | null;
  setReport: (report: WhoopReport | null) => void;
};

const ReportCtx = createContext<Ctx | null>(null);

export function ReportProvider({ children }: { children: ReactNode }) {
  const [report, setReport] = useState<WhoopReport | null>(null);
  return (
    <ReportCtx.Provider value={{ report, setReport }}>
      {children}
    </ReportCtx.Provider>
  );
}

export function useReport(): Ctx {
  const ctx = useContext(ReportCtx);
  if (!ctx) {
    throw new Error("useReport must be used inside <ReportProvider>");
  }
  return ctx;
}
```

- [ ] **Step 2: Implement `Dropzone.tsx`**

Create `apps/web/src/components/upload/Dropzone.tsx`:

```tsx
"use client";

import { clsx } from "clsx";
import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

type Props = {
  onFile: (file: File) => void;
  disabled?: boolean;
};

export function Dropzone({ onFile, disabled }: Props) {
  const onDrop = useCallback(
    (files: File[]) => {
      const file = files[0];
      if (file) onFile(file);
    },
    [onFile],
  );
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/zip": [".zip"] },
    maxFiles: 1,
    multiple: false,
    disabled,
  });

  return (
    <div
      {...getRootProps()}
      className={clsx(
        "group flex min-h-[280px] cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed border-white/15 bg-card/50 px-8 py-12 text-center transition",
        isDragActive && "border-teal bg-teal/5",
        disabled && "pointer-events-none opacity-60",
      )}
    >
      <input {...getInputProps()} />
      <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-text-3">
        Step 1
      </div>
      <h2 className="mt-2 font-mono text-3xl font-bold text-text-primary">
        Drop your <span className="text-teal">my_whoop_data</span>.zip
      </h2>
      <p className="mt-4 max-w-lg text-sm leading-relaxed text-text-2">
        Get your export from the Whoop app · Settings · Data · Export My Data.
        We analyze it in memory and never store the CSVs.
      </p>
      <p className="mt-6 text-[11px] uppercase tracking-[0.15em] text-text-3">
        {isDragActive ? "Drop it" : "or click to browse"}
      </p>
    </div>
  );
}
```

- [ ] **Step 3: Implement `UploadProgress.tsx`**

Create `apps/web/src/components/upload/UploadProgress.tsx`:

```tsx
"use client";

type Props = {
  stage: "uploading" | "parsing" | "analyzing";
};

const LABELS: Record<Props["stage"], string> = {
  uploading: "Uploading your export…",
  parsing: "Parsing CSVs…",
  analyzing: "Computing insights…",
};

export function UploadProgress({ stage }: Props) {
  return (
    <div className="flex min-h-[280px] flex-col items-center justify-center rounded-3xl bg-card px-8 py-12 text-center">
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-white/10 border-t-teal" />
      <p className="mt-6 text-sm uppercase tracking-[0.15em] text-text-2">
        {LABELS[stage]}
      </p>
    </div>
  );
}
```

- [ ] **Step 4: Implement `UploadError.tsx`**

Create `apps/web/src/components/upload/UploadError.tsx`:

```tsx
"use client";

import type { FriendlyError } from "@/lib/errors";

type Props = {
  error: FriendlyError;
  onRetry?: () => void;
};

export function UploadError({ error, onRetry }: Props) {
  return (
    <div
      role="alert"
      className="rounded-2xl border border-rec-red/30 bg-rec-red/10 px-6 py-5 text-left"
    >
      <h3 className="text-sm font-semibold text-rec-red">{error.title}</h3>
      <p className="mt-2 text-sm text-text-2">{error.description}</p>
      {error.canRetry && onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 text-xs font-bold uppercase tracking-[0.1em] text-teal hover:brightness-110"
        >
          Try again →
        </button>
      ) : null}
    </div>
  );
}
```

- [ ] **Step 5: Write the landing page**

Create `apps/web/src/app/page.tsx`:

```tsx
"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Dropzone } from "@/components/upload/Dropzone";
import { UploadError } from "@/components/upload/UploadError";
import { UploadProgress } from "@/components/upload/UploadProgress";
import { useReport } from "@/context/ReportContext";
import { ApiError, analyzeZip } from "@/lib/api";
import { friendlyError, type FriendlyError } from "@/lib/errors";

type Stage = "idle" | "uploading" | "parsing" | "analyzing" | "error";

export default function Page() {
  const router = useRouter();
  const { setReport } = useReport();
  const [stage, setStage] = useState<Stage>("idle");
  const [error, setError] = useState<FriendlyError | null>(null);

  async function handleFile(file: File) {
    setError(null);
    setStage("uploading");
    // staged UX — small delay between visual states so the user can read the progress
    setTimeout(() => setStage((s) => (s === "uploading" ? "parsing" : s)), 400);
    setTimeout(() => setStage((s) => (s === "parsing" ? "analyzing" : s)), 900);
    try {
      const report = await analyzeZip(file);
      setReport(report);
      router.push("/report");
    } catch (e) {
      if (e instanceof ApiError) {
        setError(friendlyError(e.body, e.status));
      } else {
        setError({
          title: "Network error",
          description:
            "Couldn't reach the Whoop Lens API. Check your connection and try again.",
          canRetry: true,
        });
      }
      setStage("error");
    }
  }

  const busy = stage === "uploading" || stage === "parsing" || stage === "analyzing";

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-8 px-6 py-20">
      <header className="text-center">
        <div className="font-mono text-[11px] uppercase tracking-[0.24em] text-text-3">
          WHOOP·LENS
        </div>
        <h1 className="mt-3 font-mono text-4xl font-bold leading-tight text-text-primary">
          Your Whoop data,
          <br />
          <span className="text-teal">visualized.</span>
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-sm text-text-2">
          Drop your Whoop data export ZIP and get an interactive report in seconds.
          Private by default — nothing is stored unless you choose to share it.
        </p>
      </header>
      {busy ? (
        <UploadProgress
          stage={stage === "uploading" ? "uploading" : stage === "parsing" ? "parsing" : "analyzing"}
        />
      ) : (
        <Dropzone onFile={handleFile} disabled={busy} />
      )}
      {error ? (
        <UploadError
          error={error}
          onRetry={() => {
            setError(null);
            setStage("idle");
          }}
        />
      ) : null}
    </div>
  );
}
```

- [ ] **Step 6: Wrap app in ReportProvider**

Modify `apps/web/src/app/layout.tsx` — add the provider around `{children}`:

```tsx
import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";

import { Footer } from "@/components/ui/Footer";
import { ReportProvider } from "@/context/ReportContext";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Whoop Lens — visualize your Whoop data export",
  description:
    "Open-source report generator for Whoop data exports. Not affiliated with WHOOP, Inc.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable} antialiased`}
    >
      <body className="min-h-screen flex flex-col">
        <ReportProvider>
          <main className="flex-1">{children}</main>
          <Footer />
        </ReportProvider>
      </body>
    </html>
  );
}
```

- [ ] **Step 7: Write the UploadError test**

Create `apps/web/tests/components/UploadError.test.tsx`:

```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { UploadError } from "@/components/upload/UploadError";

describe("UploadError", () => {
  it("renders title and description", () => {
    render(
      <UploadError
        error={{
          title: "File too large",
          description: "Max 50 MB.",
          canRetry: false,
        }}
      />,
    );
    expect(screen.getByText("File too large")).toBeInTheDocument();
    expect(screen.getByText(/max 50 mb/i)).toBeInTheDocument();
  });

  it("shows retry button when canRetry", () => {
    const onRetry = vi.fn();
    render(
      <UploadError
        error={{ title: "x", description: "y", canRetry: true }}
        onRetry={onRetry}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /try again/i }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("hides retry when canRetry is false", () => {
    render(
      <UploadError
        error={{ title: "x", description: "y", canRetry: false }}
        onRetry={() => {}}
      />,
    );
    expect(screen.queryByRole("button", { name: /try again/i })).toBeNull();
  });
});
```

- [ ] **Step 8: Verify end-to-end**

```bash
cd /Users/dibenkobit/projects/whoop-lens/apps/web
bun run test
bun run typecheck
bun run lint
bun run build
```

Expected: all green. Start the dev server and eyeball it:

```bash
bun run dev
```

Open http://localhost:3000 — should see the landing hero with dropzone. Kill the server with Ctrl-C.

- [ ] **Step 9: Commit**

```bash
cd /Users/dibenkobit/projects/whoop-lens
git add apps/web/
git commit -m "feat(web): add landing page with dropzone and upload flow

- ReportContext provides in-memory report state
- Dropzone using react-dropzone, accepts .zip
- Three-stage UploadProgress (uploading/parsing/analyzing)
- UploadError maps API error codes to friendly copy, retry button for 5xx
- Landing page orchestrates the flow and pushes to /report on success
- UploadError tests (3) passing"
```

---

## Task 7: Report shell + sidebar nav + header + share dialog

**Files:**
- Create: `apps/web/src/components/report/Card.tsx`
- Create: `apps/web/src/components/report/CardLabel.tsx`
- Create: `apps/web/src/components/report/ReportHeader.tsx`
- Create: `apps/web/src/components/report/Sidebar.tsx`
- Create: `apps/web/src/components/report/ReportShell.tsx`
- Create: `apps/web/src/components/report/ShareDialog.tsx`
- Create: `apps/web/src/app/report/page.tsx`

- [ ] **Step 1: Implement `Card.tsx` and `CardLabel.tsx`**

Create `apps/web/src/components/report/Card.tsx`:

```tsx
import { clsx } from "clsx";
import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  className?: string;
};

export function Card({ children, className }: Props) {
  return (
    <div className={clsx("rounded-2xl bg-card p-5", className)}>{children}</div>
  );
}
```

Create `apps/web/src/components/report/CardLabel.tsx`:

```tsx
import type { ReactNode } from "react";

export function CardLabel({ children }: { children: ReactNode }) {
  return (
    <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-3">
      {children}
    </div>
  );
}
```

- [ ] **Step 2: Implement `Sidebar.tsx`**

Create `apps/web/src/components/report/Sidebar.tsx`:

```tsx
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
```

- [ ] **Step 3: Implement `ShareDialog.tsx`**

Create `apps/web/src/components/report/ShareDialog.tsx`:

```tsx
"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { createShare } from "@/lib/api";
import type { WhoopReport } from "@/lib/types";

type Props = {
  open: boolean;
  onClose: () => void;
  report: WhoopReport;
};

export function ShareDialog({ open, onClose, report }: Props) {
  const [state, setState] = useState<"idle" | "creating" | "done" | "error">(
    "idle",
  );
  const [url, setUrl] = useState<string | null>(null);

  async function create() {
    setState("creating");
    try {
      const resp = await createShare(report);
      const fullUrl = `${window.location.origin}${resp.url}`;
      setUrl(fullUrl);
      setState("done");
    } catch {
      setState("error");
    }
  }

  function reset() {
    setState("idle");
    setUrl(null);
    onClose();
  }

  return (
    <Dialog open={open} onClose={reset} title="Share Report">
      {state === "idle" && (
        <>
          <p className="text-sm text-text-2">
            Your report will be saved for 30 days under an anonymous URL. Anyone
            with the link can view it. Nothing beyond the computed report is
            stored.
          </p>
          <div className="mt-6 flex justify-end gap-3">
            <Button variant="ghost" onClick={reset}>
              Cancel
            </Button>
            <Button onClick={create}>Create link</Button>
          </div>
        </>
      )}
      {state === "creating" && (
        <p className="py-6 text-center text-sm text-text-2">Creating link…</p>
      )}
      {state === "done" && url && (
        <>
          <p className="text-sm text-text-2">Your share link (valid 30 days):</p>
          <div className="mt-3 break-all rounded-md bg-black/40 px-3 py-2 font-mono text-xs">
            {url}
          </div>
          <div className="mt-6 flex justify-end gap-3">
            <Button
              variant="secondary"
              onClick={() => {
                void navigator.clipboard.writeText(url);
              }}
            >
              Copy
            </Button>
            <Button onClick={reset}>Done</Button>
          </div>
        </>
      )}
      {state === "error" && (
        <>
          <p className="text-sm text-rec-red">
            Couldn't create the share link. Please try again.
          </p>
          <div className="mt-6 flex justify-end gap-3">
            <Button variant="ghost" onClick={reset}>
              Close
            </Button>
            <Button onClick={create}>Retry</Button>
          </div>
        </>
      )}
    </Dialog>
  );
}
```

- [ ] **Step 4: Implement `ReportHeader.tsx`**

Create `apps/web/src/components/report/ReportHeader.tsx`:

```tsx
"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { formatPeriod } from "@/lib/format";
import type { WhoopReport } from "@/lib/types";

import { ShareDialog } from "./ShareDialog";

type Props = {
  report: WhoopReport;
  canShare: boolean;
};

export function ReportHeader({ report, canShare }: Props) {
  const [open, setOpen] = useState(false);
  return (
    <header className="mb-6 flex flex-col gap-2 border-b border-white/5 pb-6 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-3">
          Report Period
        </div>
        <div className="mt-1 text-sm text-text-primary">
          {formatPeriod(report.period.start, report.period.end)}
          <span className="ml-2 text-text-3">· {report.period.days} days</span>
        </div>
      </div>
      {canShare ? (
        <>
          <Button onClick={() => setOpen(true)}>↗ Share Report</Button>
          <ShareDialog open={open} onClose={() => setOpen(false)} report={report} />
        </>
      ) : null}
    </header>
  );
}
```

- [ ] **Step 5: Implement `ReportShell.tsx`**

Create `apps/web/src/components/report/ReportShell.tsx`:

```tsx
"use client";

import { useState, type ReactNode } from "react";

import type { WhoopReport } from "@/lib/types";

import { ReportHeader } from "./ReportHeader";
import { Sidebar, type SectionKey } from "./Sidebar";

type Props = {
  report: WhoopReport;
  canShare: boolean;
  renderSection: (key: SectionKey) => ReactNode;
};

export function ReportShell({ report, canShare, renderSection }: Props) {
  const [section, setSection] = useState<SectionKey>("overview");
  return (
    <div className="mx-auto grid max-w-7xl grid-cols-1 lg:grid-cols-[220px_1fr]">
      <Sidebar active={section} onChange={setSection} report={report} />
      <div className="px-6 py-8 lg:px-10">
        <ReportHeader report={report} canShare={canShare} />
        {renderSection(section)}
      </div>
    </div>
  );
}
```

- [ ] **Step 6: Create the `/report` route**

Create `apps/web/src/app/report/page.tsx`:

```tsx
"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { ReportShell } from "@/components/report/ReportShell";
import { useReport } from "@/context/ReportContext";

export default function ReportPage() {
  const router = useRouter();
  const { report } = useReport();

  useEffect(() => {
    if (!report) router.replace("/");
  }, [report, router]);

  if (!report) return null;

  return (
    <ReportShell
      report={report}
      canShare={true}
      renderSection={(key) => (
        <div className="rounded-2xl bg-card p-5 text-sm text-text-2">
          Section: <span className="font-mono">{key}</span> — placeholder.
        </div>
      )}
    />
  );
}
```

This is a placeholder renderer — Tasks 8–14 will fill in each section. For now, the shell is functional and the navigation works.

- [ ] **Step 7: Verify**

```bash
cd /Users/dibenkobit/projects/whoop-lens/apps/web
bun run test
bun run typecheck
bun run lint
bun run build
```

Expected: all green. Optional: `bun run dev`, upload the happy fixture via the landing page (you'll need the backend running), and verify sidebar switches sections.

- [ ] **Step 8: Commit**

```bash
cd /Users/dibenkobit/projects/whoop-lens
git add apps/web/
git commit -m "feat(web): add report shell with sidebar nav and share dialog

- Card and CardLabel primitives
- Sidebar auto-hides workouts/journal sections when null
- ReportHeader shows period + Share button (hidden on /r/[id] routes)
- ShareDialog integrates POST /share with copy-to-clipboard
- ReportShell composes sidebar + header + section renderer
- /report route reads from ReportContext, redirects to / if empty
- Section bodies are placeholder until Tasks 8-14 fill them in"
```

---

## Task 8: Overview section

**Files:**
- Create: `apps/web/src/components/report/MetricRow.tsx`
- Create: `apps/web/src/components/report/InsightCard.tsx`
- Create: `apps/web/src/components/report/sections/OverviewSection.tsx`
- Create: `apps/web/tests/components/InsightCard.test.tsx`
- Modify: `apps/web/src/app/report/page.tsx`

- [ ] **Step 1: Implement `MetricRow.tsx`**

Create `apps/web/src/components/report/MetricRow.tsx`:

```tsx
import type { Metrics } from "@/lib/types";

type Item = { label: string; value: string; unit?: string };

function Cell({ item }: { item: Item }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-[0.18em] text-text-3">
        {item.label}
      </div>
      <div className="mt-1 font-mono text-base font-bold text-text-primary">
        {item.value}
        {item.unit ? (
          <span className="ml-1 text-xs font-normal text-text-3">{item.unit}</span>
        ) : null}
      </div>
    </div>
  );
}

export function MetricRow({ metrics }: { metrics: Metrics }) {
  const items: Item[] = [
    { label: "HRV", value: Math.round(metrics.hrv_ms).toString(), unit: "ms" },
    { label: "RHR", value: Math.round(metrics.rhr_bpm).toString(), unit: "bpm" },
    { label: "Resp", value: metrics.resp_rpm.toFixed(1) },
    {
      label: "SpO₂",
      value: metrics.spo2_pct.toFixed(1),
      unit: "%",
    },
  ];
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {items.map((it) => (
        <Cell key={it.label} item={it} />
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Implement `InsightCard.tsx`**

Create `apps/web/src/components/report/InsightCard.tsx`:

```tsx
import type { Insight } from "@/lib/types";

import { Card } from "./Card";

const LABELS: Record<Insight["severity"], string> = {
  high: "HIGH PRIORITY",
  medium: "WORTH NOTICING",
  low: "OBSERVATION",
};

export function InsightCard({ insight }: { insight: Insight }) {
  return (
    <Card className="flex flex-col gap-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-teal">
        {LABELS[insight.severity]}
      </div>
      <h3 className="text-base font-semibold leading-snug text-text-primary">
        {insight.title}
      </h3>
      <div className="flex items-baseline gap-2">
        <span className="font-mono text-2xl font-bold text-text-primary">
          {insight.highlight.value}
        </span>
        {insight.highlight.unit ? (
          <span className="text-[11px] uppercase tracking-[0.15em] text-text-3">
            {insight.highlight.unit}
          </span>
        ) : null}
      </div>
      <p className="text-sm leading-relaxed text-text-2">{insight.body}</p>
    </Card>
  );
}
```

- [ ] **Step 3: Implement `OverviewSection.tsx`**

Create `apps/web/src/components/report/sections/OverviewSection.tsx`:

```tsx
import { Card } from "@/components/report/Card";
import { CardLabel } from "@/components/report/CardLabel";
import { DialRow } from "@/components/report/DialRow";
import { InsightCard } from "@/components/report/InsightCard";
import { MetricRow } from "@/components/report/MetricRow";
import type { WhoopReport } from "@/lib/types";

export function OverviewSection({ report }: { report: WhoopReport }) {
  const topInsight = report.insights[0] ?? null;
  return (
    <div className="flex flex-col gap-4">
      <DialRow dials={report.dials} />
      <Card>
        <CardLabel>Health monitor</CardLabel>
        <div className="mt-3">
          <MetricRow metrics={report.metrics} />
        </div>
      </Card>
      {topInsight ? <InsightCard insight={topInsight} /> : null}
    </div>
  );
}
```

- [ ] **Step 4: Write InsightCard test**

Create `apps/web/tests/components/InsightCard.test.tsx`:

```tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { InsightCard } from "@/components/report/InsightCard";
import type { Insight } from "@/lib/types";

describe("InsightCard", () => {
  it("renders title, highlight, and body", () => {
    const insight: Insight = {
      kind: "undersleep",
      severity: "high",
      title: "You undersleep 13% of nights",
      body: "Adding sleep is your biggest lever.",
      highlight: { value: "+30", unit: "pp" },
    };
    render(<InsightCard insight={insight} />);
    expect(screen.getByText(/undersleep 13% of nights/i)).toBeInTheDocument();
    expect(screen.getByText("+30")).toBeInTheDocument();
    expect(screen.getByText("pp")).toBeInTheDocument();
    expect(screen.getByText(/biggest lever/i)).toBeInTheDocument();
    expect(screen.getByText("HIGH PRIORITY")).toBeInTheDocument();
  });

  it("omits unit when highlight.unit is absent", () => {
    const insight: Insight = {
      kind: "late_chronotype",
      severity: "low",
      title: "Night owl",
      body: "late bedtime",
      highlight: { value: "01:00+" },
    };
    render(<InsightCard insight={insight} />);
    expect(screen.getByText("01:00+")).toBeInTheDocument();
  });
});
```

- [ ] **Step 5: Wire OverviewSection into `/report` page**

Modify `apps/web/src/app/report/page.tsx`:

```tsx
"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { ReportShell } from "@/components/report/ReportShell";
import { OverviewSection } from "@/components/report/sections/OverviewSection";
import { useReport } from "@/context/ReportContext";

export default function ReportPage() {
  const router = useRouter();
  const { report } = useReport();

  useEffect(() => {
    if (!report) router.replace("/");
  }, [report, router]);

  if (!report) return null;

  return (
    <ReportShell
      report={report}
      canShare={true}
      renderSection={(key) => {
        if (key === "overview") return <OverviewSection report={report} />;
        return (
          <div className="rounded-2xl bg-card p-5 text-sm text-text-2">
            Section: <span className="font-mono">{key}</span> — placeholder.
          </div>
        );
      }}
    />
  );
}
```

- [ ] **Step 6: Verify**

```bash
cd /Users/dibenkobit/projects/whoop-lens/apps/web
bun run test
bun run typecheck
bun run lint
bun run build
```

- [ ] **Step 7: Commit**

```bash
cd /Users/dibenkobit/projects/whoop-lens
git add apps/web/
git commit -m "feat(web): add Overview section with dials + metrics + top insight

- MetricRow: HRV / RHR / Resp / SpO2 in 4 cells
- InsightCard: severity label, title, mono highlight, body (no left border)
- OverviewSection composes DialRow + health monitor card + first insight
- InsightCard test (2) passing"
```

---

## Task 9: Recovery section

**Files:**
- Create: `apps/web/src/components/report/TrendLineChart.tsx`
- Create: `apps/web/src/components/report/DowBars.tsx`
- Create: `apps/web/src/components/report/RecoveryDistribution.tsx`
- Create: `apps/web/src/components/report/SickEpisodesList.tsx`
- Create: `apps/web/src/components/report/sections/RecoverySection.tsx`
- Modify: `apps/web/src/app/report/page.tsx`

- [ ] **Step 1: Implement `TrendLineChart.tsx`**

Create `apps/web/src/components/report/TrendLineChart.tsx`:

```tsx
"use client";

import dynamic from "next/dynamic";
import type { EChartsOption } from "echarts";

import { COLORS } from "@/lib/colors";
import type { TrendPoint } from "@/lib/types";

const ReactECharts = dynamic(() => import("echarts-for-react"), {
  ssr: false,
});

type Props = {
  trend: TrendPoint[];
  color?: string;
  height?: number;
};

export function TrendLineChart({ trend, color = COLORS.recBlue, height = 140 }: Props) {
  const dates = trend.map((p) => p.date);
  const values = trend.map((p) => (p.value === null ? null : p.value));

  const option: EChartsOption = {
    animation: true,
    animationDuration: 600,
    grid: { top: 10, right: 10, bottom: 20, left: 30 },
    xAxis: {
      type: "category",
      data: dates,
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.15)" } },
      axisLabel: { show: false },
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 100,
      splitNumber: 4,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.05)" } },
      axisLabel: { color: COLORS.text3, fontSize: 10 },
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: COLORS.card,
      borderColor: "rgba(255,255,255,0.08)",
      textStyle: { color: COLORS.textPrimary, fontSize: 11 },
    },
    series: [
      {
        type: "line",
        data: values,
        smooth: true,
        showSymbol: false,
        lineStyle: { color, width: 2 },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: `${color}55` },
              { offset: 1, color: `${color}00` },
            ],
          },
        },
        connectNulls: false,
      },
    ],
  };

  return (
    <ReactECharts
      option={option}
      style={{ height, width: "100%" }}
      notMerge
      lazyUpdate
      opts={{ renderer: "canvas" }}
    />
  );
}
```

- [ ] **Step 2: Implement `DowBars.tsx`**

Create `apps/web/src/components/report/DowBars.tsx`:

```tsx
import { COLORS, recoveryColor } from "@/lib/colors";
import type { DowEntry } from "@/lib/types";

const ORDER = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"] as const;
const LABELS: Record<(typeof ORDER)[number], string> = {
  mon: "MON",
  tue: "TUE",
  wed: "WED",
  thu: "THU",
  fri: "FRI",
  sat: "SAT",
  sun: "SUN",
};

type Props = { entries: DowEntry[] };

export function DowBars({ entries }: Props) {
  const byDow = new Map(entries.map((e) => [e.dow, e]));
  const max = Math.max(
    ...entries.map((e) => e.mean),
    1,
  );

  return (
    <div className="grid grid-cols-7 gap-2">
      {ORDER.map((dow) => {
        const e = byDow.get(dow);
        const value = e?.mean ?? 0;
        const heightPct = (value / 100) * 100; // 0-100
        const color = e ? recoveryColor(value) : COLORS.text3;
        const dim = value < (max * 0.7);
        return (
          <div key={dow} className="flex flex-col items-center gap-2">
            <div className="relative h-16 w-full">
              <div
                className="absolute inset-x-0 bottom-0 rounded-sm"
                style={{
                  backgroundColor: color,
                  height: `${Math.max(heightPct, 2)}%`,
                  opacity: dim ? 0.65 : 1,
                }}
              />
            </div>
            <div className="text-[9px] tracking-[0.1em] text-text-3">
              {LABELS[dow]}
            </div>
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 3: Implement `RecoveryDistribution.tsx`**

Create `apps/web/src/components/report/RecoveryDistribution.tsx`:

```tsx
import { COLORS } from "@/lib/colors";
import type { RecoveryDistribution as DistType } from "@/lib/types";

export function RecoveryDistribution({
  distribution,
}: {
  distribution: DistType;
}) {
  return (
    <div className="space-y-2">
      <div className="flex h-3 w-full overflow-hidden rounded-sm">
        <div
          style={{
            width: `${distribution.green}%`,
            backgroundColor: COLORS.recGreen,
          }}
        />
        <div
          style={{
            width: `${distribution.yellow}%`,
            backgroundColor: COLORS.recYellow,
          }}
        />
        <div
          style={{
            width: `${distribution.red}%`,
            backgroundColor: COLORS.recRed,
          }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-text-3">
        <span style={{ color: COLORS.recGreen }}>
          {distribution.green.toFixed(0)}% green
        </span>
        <span style={{ color: COLORS.recYellow }}>
          {distribution.yellow.toFixed(0)}% yellow
        </span>
        <span style={{ color: COLORS.recRed }}>
          {distribution.red.toFixed(0)}% red
        </span>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Implement `SickEpisodesList.tsx`**

Create `apps/web/src/components/report/SickEpisodesList.tsx`:

```tsx
import { formatDate } from "@/lib/format";
import type { SickEpisode } from "@/lib/types";

export function SickEpisodesList({
  episodes,
}: {
  episodes: SickEpisode[];
}) {
  if (episodes.length === 0) {
    return (
      <p className="text-sm text-text-3">
        No illness-like episodes detected in your data. Nice.
      </p>
    );
  }
  return (
    <ul className="space-y-2">
      {episodes.map((e) => (
        <li
          key={e.date}
          className="flex items-center justify-between rounded-md bg-black/30 px-3 py-2 text-xs"
        >
          <span className="font-mono text-text-primary">
            {formatDate(e.date)}
          </span>
          <span className="text-text-2">
            rec {e.recovery.toFixed(0)}% · rhr {Math.round(e.rhr)} · hrv{" "}
            {Math.round(e.hrv)}
            {e.skin_temp_c !== null
              ? ` · skin ${e.skin_temp_c.toFixed(1)}°C`
              : ""}
          </span>
        </li>
      ))}
    </ul>
  );
}
```

- [ ] **Step 5: Implement `RecoverySection.tsx`**

Create `apps/web/src/components/report/sections/RecoverySection.tsx`:

```tsx
import { Card } from "@/components/report/Card";
import { CardLabel } from "@/components/report/CardLabel";
import { Dial } from "@/components/report/Dial";
import { DowBars } from "@/components/report/DowBars";
import { InsightCard } from "@/components/report/InsightCard";
import { RecoveryDistribution } from "@/components/report/RecoveryDistribution";
import { SickEpisodesList } from "@/components/report/SickEpisodesList";
import { TrendLineChart } from "@/components/report/TrendLineChart";
import { COLORS, recoveryColor } from "@/lib/colors";
import type { WhoopReport } from "@/lib/types";

export function RecoverySection({ report }: { report: WhoopReport }) {
  const rec = report.dials.recovery;
  const recoveryInsights = report.insights.filter((i) =>
    [
      "sick_episodes",
      "dow_pattern",
      "travel_impact",
      "long_term_trend",
    ].includes(i.kind),
  );
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[260px_1fr]">
      <div className="flex flex-col gap-4">
        <Dial
          value={rec.value}
          max={100}
          color={recoveryColor(rec.value)}
          display={`${rec.value.toFixed(0)}%`}
          label="Avg Recovery"
          sub={`${rec.green_pct.toFixed(0)}% green days`}
        />
        <Card>
          <CardLabel>Distribution</CardLabel>
          <div className="mt-3">
            <RecoveryDistribution distribution={report.recovery.distribution} />
          </div>
        </Card>
      </div>
      <div className="flex flex-col gap-4">
        <Card>
          <CardLabel>Recovery trend</CardLabel>
          <div className="mt-3">
            <TrendLineChart trend={report.recovery.trend} color={COLORS.recBlue} />
          </div>
        </Card>
        <Card>
          <CardLabel>Day of week</CardLabel>
          <div className="mt-3">
            <DowBars entries={report.recovery.by_dow} />
          </div>
        </Card>
        <Card>
          <CardLabel>Likely illness episodes</CardLabel>
          <div className="mt-3">
            <SickEpisodesList episodes={report.recovery.sick_episodes} />
          </div>
        </Card>
        {recoveryInsights.slice(0, 2).map((i) => (
          <InsightCard key={i.kind} insight={i} />
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 6: Wire into `/report`**

Modify `apps/web/src/app/report/page.tsx` — add `RecoverySection` to the switch:

```tsx
import { RecoverySection } from "@/components/report/sections/RecoverySection";

// ... inside renderSection:
if (key === "recovery") return <RecoverySection report={report} />;
```

- [ ] **Step 7: Verify**

```bash
cd /Users/dibenkobit/projects/whoop-lens/apps/web
bun run test
bun run typecheck
bun run lint
bun run build
```

- [ ] **Step 8: Commit**

```bash
cd /Users/dibenkobit/projects/whoop-lens
git add apps/web/
git commit -m "feat(web): add Recovery section

- TrendLineChart: ECharts line with gradient fill, null-safe
- DowBars: 7-day recovery bars with color zones
- RecoveryDistribution: 3-segment green/yellow/red stacked bar
- SickEpisodesList: graceful empty state
- RecoverySection: big dial + trend + dow + sick episodes + insights"
```

---

## Task 10: Sleep section

**Files:**
- Create: `apps/web/src/components/report/SleepStageBreakdown.tsx`
- Create: `apps/web/src/components/report/ConsistencyStrip.tsx`
- Create: `apps/web/src/components/report/Hypnogram.tsx`
- Create: `apps/web/src/components/report/sections/SleepSection.tsx`
- Modify: `apps/web/src/app/report/page.tsx`

- [ ] **Step 1: Implement `SleepStageBreakdown.tsx`**

Create `apps/web/src/components/report/SleepStageBreakdown.tsx`:

```tsx
import { COLORS } from "@/lib/colors";
import { formatHours } from "@/lib/format";
import type { SleepDurations, SleepStagePct } from "@/lib/types";

type Props = {
  durations: SleepDurations;
  pct: SleepStagePct;
};

export function SleepStageBreakdown({ durations, pct }: Props) {
  const rows: {
    label: string;
    pct: number;
    minutes: number;
    tone: string;
  }[] = [
    {
      label: "Deep",
      pct: pct.deep,
      minutes: durations.deep_min,
      tone: COLORS.sleep,
    },
    {
      label: "REM",
      pct: pct.rem,
      minutes: durations.rem_min,
      tone: `${COLORS.sleep}cc`,
    },
    {
      label: "Light",
      pct: pct.light,
      minutes: durations.light_min,
      tone: `${COLORS.sleep}80`,
    },
    {
      label: "Awake",
      pct: 0, // derived from stages not explicitly, omit from bar
      minutes: durations.awake_min,
      tone: `${COLORS.sleep}40`,
    },
  ];
  return (
    <div className="space-y-3">
      {rows.map((r) => (
        <div key={r.label}>
          <div className="flex justify-between text-[11px] text-text-2">
            <span>{r.label}</span>
            <span className="font-mono">
              {formatHours(r.minutes)}
              {r.pct > 0 ? (
                <span className="ml-2 text-text-3">{r.pct.toFixed(0)}%</span>
              ) : null}
            </span>
          </div>
          <div className="mt-1 h-1.5 w-full rounded-full bg-black/40">
            <div
              className="h-full rounded-full"
              style={{
                width: `${Math.min(r.pct || 0, 100)}%`,
                backgroundColor: r.tone,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Implement `ConsistencyStrip.tsx`**

Create `apps/web/src/components/report/ConsistencyStrip.tsx`:

```tsx
import { COLORS } from "@/lib/colors";
import type { BedtimeStrip } from "@/lib/types";

type Props = { strip: BedtimeStrip[] };

// Convert "HH:MM" to hours past noon (bedtime) or hours past midnight (wake).
// Bedtime: 12:00-23:59 -> 0..11.99, 00:00-11:59 -> 12..23.99 (day-aligned 12-36h)
// We render on a 24h strip starting at 18:00 and ending at 14:00 next day.
function bedHours(hhmm: string): number {
  const [h, m] = hhmm.split(":").map(Number);
  const raw = (h ?? 0) + (m ?? 0) / 60;
  return raw >= 12 ? raw : raw + 24;
}

function wakeHours(hhmm: string): number {
  const [h, m] = hhmm.split(":").map(Number);
  const raw = (h ?? 0) + (m ?? 0) / 60;
  return raw < 12 ? raw + 24 : raw; // always treat wake as next day
}

const STRIP_START = 18; // 6pm
const STRIP_END = 38; // 2pm next day = 14+24
const STRIP_SPAN = STRIP_END - STRIP_START;

export function ConsistencyStrip({ strip }: Props) {
  if (strip.length === 0) {
    return <p className="text-sm text-text-3">Not enough data yet.</p>;
  }
  return (
    <div className="space-y-1.5">
      {strip.map((row) => {
        const bed = bedHours(row.bed_local);
        const wake = wakeHours(row.wake_local);
        const leftPct = ((bed - STRIP_START) / STRIP_SPAN) * 100;
        const widthPct = ((wake - bed) / STRIP_SPAN) * 100;
        return (
          <div key={row.date} className="flex items-center gap-3">
            <div className="w-14 text-[10px] text-text-3">{row.date.slice(5)}</div>
            <div className="relative h-3 flex-1 overflow-hidden rounded-sm bg-black/40">
              <div
                className="absolute inset-y-0"
                style={{
                  left: `${Math.max(leftPct, 0)}%`,
                  width: `${Math.max(Math.min(widthPct, 100 - leftPct), 0)}%`,
                  backgroundColor: COLORS.sleep,
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 3: Implement `Hypnogram.tsx`**

Create `apps/web/src/components/report/Hypnogram.tsx`:

```tsx
"use client";

import { COLORS } from "@/lib/colors";
import type { HypnogramNight, HypnogramStage } from "@/lib/types";

const STAGE_ROW: Record<HypnogramStage, number> = {
  awake: 0,
  rem: 1,
  light: 2,
  deep: 3,
};
const STAGE_LABEL: Record<HypnogramStage, string> = {
  awake: "Awake",
  rem: "REM",
  light: "Light",
  deep: "Deep",
};
const STAGE_COLOR: Record<HypnogramStage, string> = {
  awake: `${COLORS.sleep}40`,
  rem: `${COLORS.sleep}80`,
  light: `${COLORS.sleep}bb`,
  deep: COLORS.sleep,
};

type Props = {
  night: HypnogramNight | null;
};

export function Hypnogram({ night }: Props) {
  if (!night || night.segments.length === 0) {
    return (
      <p className="text-sm text-text-3">
        Per-night stage timeline isn't available in your export.
      </p>
    );
  }
  const start = new Date(night.start).getTime();
  const end = new Date(night.end).getTime();
  const span = Math.max(end - start, 1);

  return (
    <div className="relative h-28 w-full">
      {/* rows background */}
      <div className="absolute inset-0 flex flex-col justify-between">
        {(["awake", "rem", "light", "deep"] as HypnogramStage[]).map((s) => (
          <div
            key={s}
            className="h-[22%] border-t border-white/5 text-[9px] text-text-3"
          >
            {STAGE_LABEL[s]}
          </div>
        ))}
      </div>
      {/* segments */}
      {night.segments.map((seg) => {
        const t0 = new Date(seg.from).getTime();
        const t1 = new Date(seg.to).getTime();
        const left = ((t0 - start) / span) * 100;
        const width = ((t1 - t0) / span) * 100;
        const row = STAGE_ROW[seg.stage];
        return (
          <div
            key={`${seg.from}-${seg.stage}`}
            className="absolute h-[16%] rounded-sm"
            style={{
              left: `${left}%`,
              width: `${width}%`,
              top: `${row * 22 + 3}%`,
              backgroundColor: STAGE_COLOR[seg.stage],
            }}
          />
        );
      })}
    </div>
  );
}
```

- [ ] **Step 4: Implement `SleepSection.tsx`**

Create `apps/web/src/components/report/sections/SleepSection.tsx`:

```tsx
import { Card } from "@/components/report/Card";
import { CardLabel } from "@/components/report/CardLabel";
import { ConsistencyStrip } from "@/components/report/ConsistencyStrip";
import { Dial } from "@/components/report/Dial";
import { Hypnogram } from "@/components/report/Hypnogram";
import { InsightCard } from "@/components/report/InsightCard";
import { SleepStageBreakdown } from "@/components/report/SleepStageBreakdown";
import { COLORS } from "@/lib/colors";
import type { WhoopReport } from "@/lib/types";

export function SleepSection({ report }: { report: WhoopReport }) {
  const s = report.sleep;
  const sleepInsights = report.insights.filter((i) =>
    ["undersleep", "bedtime_consistency", "late_chronotype", "sleep_stage_quality"].includes(i.kind),
  );

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[260px_1fr]">
      <div className="flex flex-col gap-4">
        <Dial
          value={Math.min(report.dials.sleep.value, 12)}
          max={12}
          color={COLORS.sleep}
          display={`${report.dials.sleep.value.toFixed(2)}h`}
          label="Avg Sleep"
          sub={`${report.dials.sleep.performance_pct.toFixed(0)}% performance`}
        />
        <Card>
          <CardLabel>Schedule</CardLabel>
          <div className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-text-3">Avg bedtime</span>
              <span className="font-mono text-text-primary">{s.avg_bedtime}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-3">Avg wake</span>
              <span className="font-mono text-text-primary">{s.avg_wake}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-3">Bedtime std</span>
              <span className="font-mono text-text-primary">
                {s.bedtime_std_h.toFixed(1)}h
              </span>
            </div>
          </div>
        </Card>
      </div>
      <div className="flex flex-col gap-4">
        <Card>
          <CardLabel>Sleep stages</CardLabel>
          <div className="mt-3">
            <SleepStageBreakdown durations={s.avg_durations} pct={s.stage_pct} />
          </div>
        </Card>
        <Card>
          <CardLabel>Last night</CardLabel>
          <div className="mt-3">
            <Hypnogram night={s.hypnogram_sample} />
          </div>
        </Card>
        <Card>
          <CardLabel>Bedtime consistency · last 14 days</CardLabel>
          <div className="mt-3">
            <ConsistencyStrip strip={s.consistency_strip} />
          </div>
        </Card>
        {sleepInsights.slice(0, 2).map((i) => (
          <InsightCard key={i.kind} insight={i} />
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Wire into `/report`**

Modify `apps/web/src/app/report/page.tsx` — add the sleep case:

```tsx
import { SleepSection } from "@/components/report/sections/SleepSection";

// inside renderSection:
if (key === "sleep") return <SleepSection report={report} />;
```

- [ ] **Step 6: Verify + commit**

```bash
bun run test
bun run typecheck
bun run lint
bun run build
```

Then:

```bash
git add apps/web/
git commit -m "feat(web): add Sleep section

- SleepStageBreakdown: bar per stage with duration and pct
- ConsistencyStrip: 14-day bedtime strip on 18:00–14:00 axis
- Hypnogram: stage timeline, graceful null state
- SleepSection: sleep dial + schedule card + stages + hypnogram + consistency + insights"
```

---

## Task 11: Strain section

**Files:**
- Create: `apps/web/src/components/report/StrainDistribution.tsx`
- Create: `apps/web/src/components/report/sections/StrainSection.tsx`
- Modify: `apps/web/src/app/report/page.tsx`

- [ ] **Step 1: Implement `StrainDistribution.tsx`**

Create `apps/web/src/components/report/StrainDistribution.tsx`:

```tsx
import { COLORS } from "@/lib/colors";
import type { StrainDistribution as DistType } from "@/lib/types";

const ROWS: {
  key: keyof DistType;
  label: string;
  hint: string;
  tint: number;
}[] = [
  { key: "light", label: "Light", hint: "0–9", tint: 0.4 },
  { key: "moderate", label: "Moderate", hint: "10–13", tint: 0.65 },
  { key: "high", label: "High", hint: "14–17", tint: 0.85 },
  { key: "all_out", label: "All Out", hint: "18–21", tint: 1 },
];

export function StrainDistribution({ distribution }: { distribution: DistType }) {
  return (
    <div className="space-y-2">
      {ROWS.map((row) => {
        const value = distribution[row.key];
        return (
          <div key={row.key} className="flex items-center gap-3 text-xs">
            <div className="w-20 text-text-3">{row.label}</div>
            <div className="relative h-2 flex-1 overflow-hidden rounded-sm bg-black/40">
              <div
                className="h-full rounded-sm"
                style={{
                  width: `${value}%`,
                  backgroundColor: COLORS.strain,
                  opacity: row.tint,
                }}
              />
            </div>
            <div className="w-10 text-right font-mono text-text-2">
              {value.toFixed(0)}%
            </div>
            <div className="w-12 text-text-3">{row.hint}</div>
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 2: Implement `StrainSection.tsx`**

Create `apps/web/src/components/report/sections/StrainSection.tsx`:

```tsx
import { Card } from "@/components/report/Card";
import { CardLabel } from "@/components/report/CardLabel";
import { Dial } from "@/components/report/Dial";
import { InsightCard } from "@/components/report/InsightCard";
import { StrainDistribution } from "@/components/report/StrainDistribution";
import { TrendLineChart } from "@/components/report/TrendLineChart";
import { COLORS } from "@/lib/colors";
import type { WhoopReport } from "@/lib/types";

export function StrainSection({ report }: { report: WhoopReport }) {
  const d = report.dials.strain;
  const strainInsights = report.insights.filter((i) =>
    ["overtraining", "workout_mix"].includes(i.kind),
  );
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[260px_1fr]">
      <div className="flex flex-col gap-4">
        <Dial
          value={d.value}
          max={21}
          color={COLORS.strain}
          display={d.value.toFixed(1)}
          label="Avg Strain"
          sub={d.label.replace("_", " ")}
        />
      </div>
      <div className="flex flex-col gap-4">
        <Card>
          <CardLabel>Strain trend</CardLabel>
          <div className="mt-3">
            <TrendLineChart
              trend={report.strain.trend}
              color={COLORS.strain}
            />
          </div>
        </Card>
        <Card>
          <CardLabel>Distribution by zone</CardLabel>
          <div className="mt-3">
            <StrainDistribution distribution={report.strain.distribution} />
          </div>
        </Card>
        {strainInsights.map((i) => (
          <InsightCard key={i.kind} insight={i} />
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Wire + verify + commit**

Modify `apps/web/src/app/report/page.tsx`:

```tsx
import { StrainSection } from "@/components/report/sections/StrainSection";

// inside renderSection:
if (key === "strain") return <StrainSection report={report} />;
```

```bash
bun run test && bun run typecheck && bun run lint && bun run build
git add apps/web/
git commit -m "feat(web): add Strain section with distribution and trend"
```

---

## Task 12: Workouts section

**Files:**
- Create: `apps/web/src/components/report/WorkoutsList.tsx`
- Create: `apps/web/src/components/report/TopStrainDays.tsx`
- Create: `apps/web/src/components/report/sections/WorkoutsSection.tsx`
- Modify: `apps/web/src/app/report/page.tsx`

- [ ] **Step 1: Implement `WorkoutsList.tsx`**

Create `apps/web/src/components/report/WorkoutsList.tsx`:

```tsx
import { formatHours } from "@/lib/format";
import type { ActivityAgg } from "@/lib/types";

export function WorkoutsList({ items }: { items: ActivityAgg[] }) {
  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li
          key={item.name}
          className="grid grid-cols-[1fr_80px_80px_60px] items-center gap-3 text-xs"
        >
          <div className="truncate text-text-primary">{item.name}</div>
          <div className="text-right font-mono text-text-2">{item.count}×</div>
          <div className="text-right font-mono text-text-2">
            {formatHours(item.total_min)}
          </div>
          <div className="text-right font-mono text-text-3">
            {item.pct_of_total_strain.toFixed(0)}%
          </div>
        </li>
      ))}
    </ul>
  );
}
```

- [ ] **Step 2: Implement `TopStrainDays.tsx`**

Create `apps/web/src/components/report/TopStrainDays.tsx`:

```tsx
import { recoveryColor } from "@/lib/colors";
import { formatDate } from "@/lib/format";
import type { TopStrainDay } from "@/lib/types";

export function TopStrainDays({ days }: { days: TopStrainDay[] }) {
  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="text-[10px] uppercase tracking-[0.14em] text-text-3">
          <th className="text-left">Date</th>
          <th className="text-right">Strain</th>
          <th className="text-right">Rec</th>
          <th className="text-right">Next</th>
        </tr>
      </thead>
      <tbody>
        {days.map((d) => (
          <tr key={d.date} className="border-t border-white/5">
            <td className="py-1.5 text-text-2">{formatDate(d.date)}</td>
            <td className="py-1.5 text-right font-mono text-text-primary">
              {d.day_strain.toFixed(1)}
            </td>
            <td
              className="py-1.5 text-right font-mono"
              style={{ color: recoveryColor(d.recovery) }}
            >
              {d.recovery.toFixed(0)}%
            </td>
            <td
              className="py-1.5 text-right font-mono"
              style={{
                color:
                  d.next_recovery === null
                    ? "var(--color-text-3)"
                    : recoveryColor(d.next_recovery),
              }}
            >
              {d.next_recovery === null
                ? "—"
                : `${d.next_recovery.toFixed(0)}%`}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

- [ ] **Step 3: Implement `WorkoutsSection.tsx`**

Create `apps/web/src/components/report/sections/WorkoutsSection.tsx`:

```tsx
import { Card } from "@/components/report/Card";
import { CardLabel } from "@/components/report/CardLabel";
import { TopStrainDays } from "@/components/report/TopStrainDays";
import { WorkoutsList } from "@/components/report/WorkoutsList";
import type { WhoopReport } from "@/lib/types";

export function WorkoutsSection({ report }: { report: WhoopReport }) {
  if (report.workouts === null) {
    return (
      <p className="text-sm text-text-3">
        No workouts found in this export.
      </p>
    );
  }
  const { by_activity, top_strain_days, total } = report.workouts;
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <Card>
        <CardLabel>By activity · {total} total</CardLabel>
        <div className="mt-3">
          <WorkoutsList items={by_activity} />
        </div>
      </Card>
      <Card>
        <CardLabel>Top 10 strain days</CardLabel>
        <div className="mt-3">
          <TopStrainDays days={top_strain_days} />
        </div>
      </Card>
    </div>
  );
}
```

- [ ] **Step 4: Wire + verify + commit**

Modify `apps/web/src/app/report/page.tsx`:

```tsx
import { WorkoutsSection } from "@/components/report/sections/WorkoutsSection";

// inside renderSection:
if (key === "workouts") return <WorkoutsSection report={report} />;
```

```bash
bun run test && bun run typecheck && bun run lint && bun run build
git add apps/web/
git commit -m "feat(web): add Workouts section with activity rollup and top strain days"
```

---

## Task 13: Trends section (monthly + first-vs-last comparison)

**Files:**
- Create: `apps/web/src/components/report/MonthlyHeatmap.tsx`
- Create: `apps/web/src/components/report/FirstVsLast.tsx`
- Create: `apps/web/src/components/report/sections/TrendsSection.tsx`
- Modify: `apps/web/src/app/report/page.tsx`

- [ ] **Step 1: Implement `MonthlyHeatmap.tsx`**

Create `apps/web/src/components/report/MonthlyHeatmap.tsx`:

```tsx
import { recoveryColor } from "@/lib/colors";
import type { MonthlyAgg } from "@/lib/types";

export function MonthlyHeatmap({ monthly }: { monthly: MonthlyAgg[] }) {
  if (monthly.length === 0) {
    return <p className="text-sm text-text-3">Not enough data for monthly trends.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] text-xs">
        <thead>
          <tr className="text-[10px] uppercase tracking-[0.12em] text-text-3">
            <th className="text-left">Month</th>
            <th className="text-right">Recovery</th>
            <th className="text-right">HRV</th>
            <th className="text-right">RHR</th>
            <th className="text-right">Sleep</th>
          </tr>
        </thead>
        <tbody>
          {monthly.map((m) => (
            <tr key={m.month} className="border-t border-white/5">
              <td className="py-2 font-mono text-text-2">{m.month}</td>
              <td
                className="py-2 text-right font-mono font-bold"
                style={{ color: recoveryColor(m.recovery) }}
              >
                {m.recovery.toFixed(0)}%
              </td>
              <td className="py-2 text-right font-mono text-text-primary">
                {m.hrv.toFixed(0)}
              </td>
              <td className="py-2 text-right font-mono text-text-primary">
                {m.rhr.toFixed(1)}
              </td>
              <td className="py-2 text-right font-mono text-text-primary">
                {m.sleep_h.toFixed(2)}h
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 2: Implement `FirstVsLast.tsx`**

Create `apps/web/src/components/report/FirstVsLast.tsx`:

```tsx
import type { TrendComparison } from "@/lib/types";

type Row = {
  label: string;
  first: string;
  last: string;
  delta: string;
  betterIfHigher: boolean;
  numericDelta: number;
};

function arrowColor(positive: boolean): string {
  return positive ? "var(--color-rec-green)" : "var(--color-rec-red)";
}

function formatHours(h: number): string {
  return `${h.toFixed(2)}h`;
}

export function FirstVsLast({ comparison }: { comparison: TrendComparison }) {
  const rows: Row[] = [
    {
      label: "Bedtime (hours past noon)",
      first: comparison.bedtime_h[0].toFixed(2),
      last: comparison.bedtime_h[1].toFixed(2),
      delta: (comparison.bedtime_h[1] - comparison.bedtime_h[0]).toFixed(2),
      betterIfHigher: false, // earlier bedtime = lower number = better
      numericDelta: comparison.bedtime_h[1] - comparison.bedtime_h[0],
    },
    {
      label: "Sleep duration",
      first: formatHours(comparison.sleep_h[0]),
      last: formatHours(comparison.sleep_h[1]),
      delta: `${(comparison.sleep_h[1] - comparison.sleep_h[0]).toFixed(2)}h`,
      betterIfHigher: true,
      numericDelta: comparison.sleep_h[1] - comparison.sleep_h[0],
    },
    {
      label: "Resting HR",
      first: `${comparison.rhr[0].toFixed(1)} bpm`,
      last: `${comparison.rhr[1].toFixed(1)} bpm`,
      delta: `${(comparison.rhr[1] - comparison.rhr[0]).toFixed(1)}`,
      betterIfHigher: false,
      numericDelta: comparison.rhr[1] - comparison.rhr[0],
    },
    {
      label: "Workouts (60d window)",
      first: comparison.workouts[0].toString(),
      last: comparison.workouts[1].toString(),
      delta: (comparison.workouts[1] - comparison.workouts[0]).toString(),
      betterIfHigher: true,
      numericDelta: comparison.workouts[1] - comparison.workouts[0],
    },
  ];
  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="text-[10px] uppercase tracking-[0.12em] text-text-3">
          <th className="text-left">Metric</th>
          <th className="text-right">First 60 days</th>
          <th className="text-right">Last 60 days</th>
          <th className="text-right">Δ</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => {
          const improved = row.betterIfHigher
            ? row.numericDelta > 0
            : row.numericDelta < 0;
          return (
            <tr key={row.label} className="border-t border-white/5">
              <td className="py-2 text-text-2">{row.label}</td>
              <td className="py-2 text-right font-mono text-text-3">
                {row.first}
              </td>
              <td className="py-2 text-right font-mono text-text-primary">
                {row.last}
              </td>
              <td
                className="py-2 text-right font-mono font-bold"
                style={{ color: arrowColor(improved) }}
              >
                {row.numericDelta >= 0 ? "+" : ""}
                {row.delta}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
```

- [ ] **Step 3: Implement `TrendsSection.tsx`**

Create `apps/web/src/components/report/sections/TrendsSection.tsx`:

```tsx
import { Card } from "@/components/report/Card";
import { CardLabel } from "@/components/report/CardLabel";
import { FirstVsLast } from "@/components/report/FirstVsLast";
import { InsightCard } from "@/components/report/InsightCard";
import { MonthlyHeatmap } from "@/components/report/MonthlyHeatmap";
import type { WhoopReport } from "@/lib/types";

export function TrendsSection({ report }: { report: WhoopReport }) {
  const trendInsights = report.insights.filter((i) =>
    ["long_term_trend"].includes(i.kind),
  );
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardLabel>Month by month</CardLabel>
        <div className="mt-3">
          <MonthlyHeatmap monthly={report.trends.monthly} />
        </div>
      </Card>
      <Card>
        <CardLabel>First 60 days vs last 60 days</CardLabel>
        <div className="mt-3">
          <FirstVsLast comparison={report.trends.first_vs_last_60d} />
        </div>
      </Card>
      {trendInsights.map((i) => (
        <InsightCard key={i.kind} insight={i} />
      ))}
    </div>
  );
}
```

- [ ] **Step 4: Wire + verify + commit**

Modify `apps/web/src/app/report/page.tsx`:

```tsx
import { TrendsSection } from "@/components/report/sections/TrendsSection";

// inside renderSection:
if (key === "trends") return <TrendsSection report={report} />;
```

```bash
bun run test && bun run typecheck && bun run lint && bun run build
git add apps/web/
git commit -m "feat(web): add Trends section with monthly table and first-vs-last comparison"
```

---

## Task 14: Journal section

**Files:**
- Create: `apps/web/src/components/report/JournalList.tsx`
- Create: `apps/web/src/components/report/sections/JournalSection.tsx`
- Modify: `apps/web/src/app/report/page.tsx`

- [ ] **Step 1: Implement `JournalList.tsx`**

Create `apps/web/src/components/report/JournalList.tsx`:

```tsx
import type { JournalQuestionAgg } from "@/lib/types";

function delta(
  yes: number | null,
  no: number | null,
): { value: string; tone: string } {
  if (yes === null || no === null) {
    return { value: "—", tone: "var(--color-text-3)" };
  }
  const d = yes - no;
  const sign = d >= 0 ? "+" : "";
  return {
    value: `${sign}${d.toFixed(0)}`,
    tone: d >= 0 ? "var(--color-rec-green)" : "var(--color-rec-red)",
  };
}

export function JournalList({
  questions,
}: {
  questions: JournalQuestionAgg[];
}) {
  if (questions.length === 0) {
    return <p className="text-sm text-text-3">No journal entries logged.</p>;
  }
  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="text-[10px] uppercase tracking-[0.12em] text-text-3">
          <th className="text-left">Question</th>
          <th className="text-right">Yes</th>
          <th className="text-right">No</th>
          <th className="text-right">ΔRec</th>
        </tr>
      </thead>
      <tbody>
        {questions.map((q) => {
          const d = delta(q.mean_rec_yes, q.mean_rec_no);
          return (
            <tr key={q.question} className="border-t border-white/5">
              <td className="py-2 text-text-2">{q.question}</td>
              <td className="py-2 text-right font-mono text-text-primary">
                {q.yes}
              </td>
              <td className="py-2 text-right font-mono text-text-3">
                {q.no}
              </td>
              <td
                className="py-2 text-right font-mono font-bold"
                style={{ color: d.tone }}
              >
                {d.value}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
```

- [ ] **Step 2: Implement `JournalSection.tsx`**

Create `apps/web/src/components/report/sections/JournalSection.tsx`:

```tsx
import { Card } from "@/components/report/Card";
import { CardLabel } from "@/components/report/CardLabel";
import { JournalList } from "@/components/report/JournalList";
import type { WhoopReport } from "@/lib/types";

export function JournalSection({ report }: { report: WhoopReport }) {
  if (report.journal === null) {
    return (
      <p className="text-sm text-text-3">No journal data in this export.</p>
    );
  }
  const { days_logged, questions, note } = report.journal;
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardLabel>Journal · {days_logged} days logged</CardLabel>
        <p className="mt-2 text-sm text-text-2">{note}</p>
        <div className="mt-4">
          <JournalList questions={questions} />
        </div>
      </Card>
    </div>
  );
}
```

- [ ] **Step 3: Wire + verify + commit**

Modify `apps/web/src/app/report/page.tsx`:

```tsx
import { JournalSection } from "@/components/report/sections/JournalSection";

// inside renderSection:
if (key === "journal") return <JournalSection report={report} />;
```

```bash
bun run test && bun run typecheck && bun run lint && bun run build
git add apps/web/
git commit -m "feat(web): add Journal section"
```

---

## Task 15: Shared report route `/r/[id]` + not-found

**Files:**
- Create: `apps/web/src/app/r/[id]/page.tsx`
- Create: `apps/web/src/app/r/[id]/not-found.tsx`

- [ ] **Step 1: Create the not-found page**

Create `apps/web/src/app/r/[id]/not-found.tsx`:

```tsx
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-xl px-6 py-24 text-center">
      <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-text-3">
        404
      </div>
      <h1 className="mt-3 font-mono text-3xl font-bold text-text-primary">
        This report no longer exists
      </h1>
      <p className="mt-4 text-sm text-text-2">
        Shared reports live for 30 days. It may have expired, or the link may be
        wrong.
      </p>
      <Link
        href="/"
        className="mt-8 inline-block text-xs font-bold uppercase tracking-[0.1em] text-teal hover:brightness-110"
      >
        Upload your own →
      </Link>
    </div>
  );
}
```

- [ ] **Step 2: Create the shared report page**

Create `apps/web/src/app/r/[id]/page.tsx`:

```tsx
import { notFound } from "next/navigation";

import { getSharedReport } from "@/lib/api";

import { SharedReportView } from "./SharedReportView";

export const dynamic = "force-dynamic";

type Params = { id: string };

export default async function Page({
  params,
}: {
  params: Promise<Params>;
}) {
  const { id } = await params;
  const report = await getSharedReport(id);
  if (!report) notFound();
  return <SharedReportView report={report} />;
}
```

Create `apps/web/src/app/r/[id]/SharedReportView.tsx`:

```tsx
"use client";

import { ReportShell } from "@/components/report/ReportShell";
import { JournalSection } from "@/components/report/sections/JournalSection";
import { OverviewSection } from "@/components/report/sections/OverviewSection";
import { RecoverySection } from "@/components/report/sections/RecoverySection";
import { SleepSection } from "@/components/report/sections/SleepSection";
import { StrainSection } from "@/components/report/sections/StrainSection";
import { TrendsSection } from "@/components/report/sections/TrendsSection";
import { WorkoutsSection } from "@/components/report/sections/WorkoutsSection";
import type { WhoopReport } from "@/lib/types";

export function SharedReportView({ report }: { report: WhoopReport }) {
  return (
    <ReportShell
      report={report}
      canShare={false}
      renderSection={(key) => {
        switch (key) {
          case "overview":
            return <OverviewSection report={report} />;
          case "recovery":
            return <RecoverySection report={report} />;
          case "sleep":
            return <SleepSection report={report} />;
          case "strain":
            return <StrainSection report={report} />;
          case "trends":
            return <TrendsSection report={report} />;
          case "workouts":
            return <WorkoutsSection report={report} />;
          case "journal":
            return <JournalSection report={report} />;
        }
      }}
    />
  );
}
```

- [ ] **Step 3: Refactor `/report/page.tsx` to reuse `SharedReportView`**

This ensures both routes use the same section dispatcher. Modify `apps/web/src/app/report/page.tsx`:

```tsx
"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { SharedReportView } from "@/app/r/[id]/SharedReportView";
import { ReportShell } from "@/components/report/ReportShell";
import { JournalSection } from "@/components/report/sections/JournalSection";
import { OverviewSection } from "@/components/report/sections/OverviewSection";
import { RecoverySection } from "@/components/report/sections/RecoverySection";
import { SleepSection } from "@/components/report/sections/SleepSection";
import { StrainSection } from "@/components/report/sections/StrainSection";
import { TrendsSection } from "@/components/report/sections/TrendsSection";
import { WorkoutsSection } from "@/components/report/sections/WorkoutsSection";
import { useReport } from "@/context/ReportContext";

export default function ReportPage() {
  const router = useRouter();
  const { report } = useReport();

  useEffect(() => {
    if (!report) router.replace("/");
  }, [report, router]);

  if (!report) return null;

  return (
    <ReportShell
      report={report}
      canShare={true}
      renderSection={(key) => {
        switch (key) {
          case "overview":
            return <OverviewSection report={report} />;
          case "recovery":
            return <RecoverySection report={report} />;
          case "sleep":
            return <SleepSection report={report} />;
          case "strain":
            return <StrainSection report={report} />;
          case "trends":
            return <TrendsSection report={report} />;
          case "workouts":
            return <WorkoutsSection report={report} />;
          case "journal":
            return <JournalSection report={report} />;
        }
      }}
    />
  );
}
```

Note: we don't actually import `SharedReportView` from `/report/page.tsx` — each page wires its own sections. The explicit duplication is intentional and keeps the two routes independent. Remove the import line if you added it.

- [ ] **Step 4: Verify + commit**

```bash
bun run test && bun run typecheck && bun run lint && bun run build
git add apps/web/
git commit -m "feat(web): add shared report route /r/[id]

- Server component fetches from API with cache: no-store
- SharedReportView (client) renders the full section shell
- not-found.tsx shows friendly expired/missing page
- Share button is hidden on shared routes (canShare=false)
- /report page uses the same section dispatcher with full switch"
```

---

## Task 16: `/about` page

**Files:**
- Create: `apps/web/src/app/about/page.tsx`

- [ ] **Step 1: Create the page**

Create `apps/web/src/app/about/page.tsx`:

```tsx
import Link from "next/link";

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-2xl px-6 py-16">
      <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-text-3">
        About
      </div>
      <h1 className="mt-3 font-mono text-3xl font-bold text-text-primary">
        Whoop Lens
      </h1>
      <p className="mt-6 text-sm leading-relaxed text-text-2">
        Whoop Lens is an open-source web app that takes a Whoop data export ZIP
        and turns it into a visual report styled after the Whoop app. Drop your
        file, get insights in seconds. Nothing is stored unless you explicitly
        share a report.
      </p>
      <h2 className="mt-10 text-sm font-bold uppercase tracking-[0.1em] text-text-2">
        How it works
      </h2>
      <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-text-2">
        <li>Export your data from Whoop (Settings · Data · Export My Data).</li>
        <li>Drop the ZIP onto the landing page.</li>
        <li>
          We parse it in memory, compute the metrics and insights, and render
          the report. Your CSVs never hit our database.
        </li>
        <li>
          If you want to share the report, click <em>Share</em>. That saves the
          computed JSON (no CSVs) for 30 days under an anonymous URL.
        </li>
      </ol>
      <h2 className="mt-10 text-sm font-bold uppercase tracking-[0.1em] text-text-2">
        What the export should look like
      </h2>
      <p className="mt-3 text-sm text-text-2">
        Your ZIP should contain these files at the top level:
      </p>
      <ul className="mt-2 list-disc space-y-1 pl-5 font-mono text-xs text-text-primary">
        <li>physiological_cycles.csv (required)</li>
        <li>sleeps.csv (required)</li>
        <li>workouts.csv (optional)</li>
        <li>journal_entries.csv (optional)</li>
      </ul>
      <h2 className="mt-10 text-sm font-bold uppercase tracking-[0.1em] text-text-2">
        Privacy
      </h2>
      <p className="mt-3 text-sm text-text-2">
        We don't log, track, or analyze usage. No cookies, no accounts. Shared
        reports expire after 30 days and we only store the computed aggregates
        (never the raw CSVs).
      </p>
      <h2 className="mt-10 text-sm font-bold uppercase tracking-[0.1em] text-text-2">
        Disclaimer
      </h2>
      <p className="mt-3 text-sm text-text-2">
        Whoop Lens is an independent open-source project. Not affiliated with,
        endorsed by, or sponsored by WHOOP, Inc. WHOOP is a trademark of WHOOP,
        Inc. No Whoop source code, logos, or proprietary assets are used in this
        project.
      </p>
      <Link
        href="/"
        className="mt-10 inline-block text-xs font-bold uppercase tracking-[0.1em] text-teal hover:brightness-110"
      >
        ← Back to upload
      </Link>
    </div>
  );
}
```

- [ ] **Step 2: Verify + commit**

```bash
bun run test && bun run typecheck && bun run lint && bun run build
git add apps/web/
git commit -m "feat(web): add /about page with disclaimer and how-it-works"
```

---

## Task 17: Wire env, next.config, and deploy

**Files:**
- Create: `apps/web/.env.local.example`
- Modify: `apps/web/next.config.ts` (if needed)
- Modify: `apps/web/package.json` (add `NEXT_PUBLIC_API_URL` note)
- Create: `apps/web/README.md` (deploy notes)

- [ ] **Step 1: Document env**

Create `apps/web/.env.local.example`:

```
# Public URL of the Whoop Lens API — required at build time
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Create `apps/web/README.md`:

```markdown
# whoop-lens-web

Next.js 16 frontend for [Whoop Lens](https://whooplens.app). Consumes the
FastAPI backend in `../api`.

## Dev

```bash
bun install
cp .env.local.example .env.local  # edit if your API runs on a non-default port
bun run dev
```

Make sure the backend is running on `http://localhost:8000` first.

## Test

```bash
bun run test
bun run typecheck
bun run lint
bun run build
```

## Deploy (Vercel)

1. Connect this repo to Vercel
2. Root directory = `apps/web`
3. Framework preset = Next.js (auto-detected)
4. Environment variables:
   - `NEXT_PUBLIC_API_URL=https://api.whooplens.app`
5. Deploy. PR previews are automatic.
```

- [ ] **Step 2: Update `next.config.ts` if needed**

Open `apps/web/next.config.ts`. By default Next 16 handles ECharts without transpilePackages, but if the build complains about ESM/CJS mismatch for `echarts-for-react`, add:

```ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    reactCompiler: true,
  },
};

export default nextConfig;
```

Only add what's missing — don't overwrite existing config.

- [ ] **Step 3: Add a test:url script**

In `apps/web/package.json` scripts section, add:

```json
"check": "biome check && tsc --noEmit && vitest run && next build"
```

This is the single command the CI job will run (Task 18 will add it).

- [ ] **Step 4: Verify + commit**

```bash
bun run check
git add apps/web/
git commit -m "chore(web): add env example, README, and unified 'check' script"
```

---

## Task 18: GitHub Actions CI for the web app

**Files:**
- Modify: `.github/workflows/ci.yml` (add web job)

- [ ] **Step 1: Read existing CI file**

Read `/Users/dibenkobit/projects/whoop-lens/.github/workflows/ci.yml` — it should already have an `api` job from the backend plan. Add a parallel `web` job:

```yaml
  web:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apps/web
    env:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v2
      - run: bun install --frozen-lockfile
      - run: bun run lint
      - run: bun run typecheck
      - run: bun run test
      - run: bun run build
```

The file should now have `api` and `web` jobs running in parallel.

- [ ] **Step 2: Commit**

```bash
cd /Users/dibenkobit/projects/whoop-lens
git add .github/
git commit -m "ci: add web job (biome + tsc + vitest + next build)"
```

---

## Final verification checklist

After Task 18, run this end-to-end smoke from the repo root:

```bash
# Backend still running from Task 0?
curl -s http://localhost:8000/healthz

# Frontend dev server
cd /Users/dibenkobit/projects/whoop-lens/apps/web
bun run dev &
sleep 4
curl -s http://localhost:3000 | grep -i "whoop.*lens"
kill %1
```

Expected:
- `/healthz` returns `{"ok":true,"db":"ok"}`
- Landing HTML contains "Whoop Lens" or "WHOOP·LENS"

**Manual smoke test (5 minutes):**
1. `bun run dev` in `apps/web/`
2. Open http://localhost:3000
3. Drop the happy fixture zip from the backend (`apps/api/tests/fixtures/zips/happy.zip`)
4. Watch the upload progress, land on `/report`
5. Click each sidebar section — all should render without console errors
6. Click "Share Report" → confirm dialog → copy URL → open in new tab — shared view should render identically, without share button

**Full suite green:**

```bash
cd /Users/dibenkobit/projects/whoop-lens
cd apps/web && bun run check
cd ../api && uv run pytest -q && uv run pyright && uv run ruff check
```

All clean.

---

## Self-review notes

**Spec coverage:**
- §4 routes — `/`, `/report`, `/r/[id]`, `/about` — Tasks 6, 7, 15, 16
- §4 components — every named component has a creation task
- §4 Share dialog — Task 7
- §5 API contract — Task 2 (types) + Task 3 (api.ts)
- §6 errors — Task 3 (lib/errors.ts) + Task 6 (UploadError wiring)
- §7 frontend testing — Vitest + utility tests (Task 3) + component smoke tests (Tasks 4, 5, 6, 8)
- §8 deployment — Task 17 (env, README, check script) + Task 18 (CI)
- §10 visual system — Task 1 (palette), Task 5 (dial), and every section task applies the grammar
- §11 insights — all 10 kinds rendered by `InsightCard` (Task 8), distributed across Overview / Recovery / Sleep / Strain / Trends sections (Tasks 8, 9, 10, 11, 13)

**Placeholder scan:** none. Every step has concrete code.

**Type consistency:** `WhoopReport`, `Insight`, `SleepDial`/`RecoveryDial`/`StrainDial`, `HypnogramSegment.from` are all mentioned consistently across tasks.

**Dependency order:** each task only builds on previous tasks. Landing (6) needs ReportContext + Dropzone + api (3). Shell (7) needs Card + DialRow + ShareDialog. Each section (8–14) needs ReportShell and the relevant domain components from Task 5.

**Known compromises:**
- Hypnogram only renders if `hypnogram_sample !== null` — the backend currently returns null for this field in v1 (per Task 10 in the backend plan), so the Hypnogram card will always show the null state until the backend's sleep analysis learns to emit per-night stage segments.
- `HrZonesBar` is listed in the file map but intentionally skipped — the backend's `WorkoutsSection` doesn't expose per-workout HR zone data (only per-activity aggregates), so the chart would have nothing to render.
- No Playwright e2e — the manual smoke test in the final checklist is the v1 replacement. Add Playwright in v1.1 once UI stabilizes.
- Vitest/testing-library React 19 compatibility: if `jsdom` throws warnings about `act`, switch to `happy-dom` in `vitest.config.ts` (Task 3).
