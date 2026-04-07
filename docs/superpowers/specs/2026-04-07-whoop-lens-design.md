# Whoop Lens — Design Doc

**Status**: Draft for review
**Date**: 2026-04-07
**Author**: Brainstormed with Claude

---

## 1. Product summary

**Whoop Lens** is an open-source web app that takes a Whoop data export ZIP and turns it into a visual report styled after Whoop's own design language. Anyone can drop in their `my_whoop_data_*.zip`, get an interactive dashboard with their key metrics and insights, and optionally generate a 30-day shareable link.

### Core principles

1. **Privacy first** — no auth, no tracking, no analytics. Raw CSVs never persisted; only computed JSON aggregates can be saved, and only when the user explicitly clicks Share.
2. **Whoop-native look** — exact brand colors, three-dial hero, dark canvas, the same visual grammar as the Whoop app, with a clear "Not affiliated with WHOOP, Inc." disclaimer everywhere.
3. **Open source, easy self-host** — fork → connect Vercel + Railway → done. MIT license.
4. **YAGNI** — no LLM, no comparison-to-others, no accounts, no email digests, no premium tier. A really good single-purpose tool.

### MVP scope

- Upload ZIP → parse → compute → render report
- 7 sections in the report: Overview, Recovery, Sleep, Strain, Trends, Workouts, Journal
- Insights engine — 10 rule-based insights derived from real data analysis
- Lazy share button → POST to backend → 30-day TTL Postgres row → `/r/<short-id>` URL
- `/about` page with disclaimer + privacy statement + format reference
- Strict required-files validation, soft optional handling for `workouts.csv` / `journal_entries.csv`

### Out of scope (v1)

- Accounts, login, password reset
- LLM/AI summary
- Comparison to population norms
- Email digests, weekly notifications
- Multiple file format support beyond current Whoop export
- Other devices (Garmin, Oura, Apple Health)
- Mobile-native app (responsive web is enough)
- i18n (English only)

### Success criteria

- A Whoop user can upload their export and within 5 seconds see a dashboard that looks like an extension of the Whoop app
- The 10 key insights from the analysis (see §11) are surfaced automatically and clearly
- Anyone can self-host with a fork + two cloud connects, no manual ops
- Open-source repo gets external contributors within 3 months

---

## 2. High-level architecture

Two deployable units, no shared package, native cloud deploys.

```
~/projects/whoop-lens/
├── apps/
│   ├── web/                    # Next.js 16.2.2 + React 19.2.4 + Tailwind v4 + ECharts
│   └── api/                    # FastAPI 0.135.3 + pandas + numpy + scipy
├── .github/workflows/ci.yml
├── biome.json
├── package.json                # Bun workspaces root
├── README.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── LICENSE                     # MIT
└── docs/
    ├── architecture.md
    ├── insights.md
    └── whoop-format.md
```

**Why this shape**

- `apps/web` → Vercel (auto-detected Next.js, no `vercel.json` needed)
- `apps/api` → Railway (auto-detected Python via `pyproject.toml`, no Dockerfile needed)
- No `packages/types` — the API surface is 3 endpoints; types are hand-written in `apps/web/src/lib/types.ts` and mirrored 1:1 by Pydantic schemas in `apps/api/app/models/`. Single source of truth lives mentally and via tests, not via code generation.
- Bun workspaces for the JS side; Python lives self-contained inside `apps/api` with `uv` for package management.

**Inter-service communication**

- Single REST API: `POST /analyze`, `POST /share`, `GET /r/{id}`, `GET /healthz`
- No websockets, no SSE — analysis is synchronous (~1–3 s for 1 year of data)
- Web makes requests directly to API. CORS-allowed origin = the Vercel URL set via env var.

**Environments**

- **Local dev**: `bun dev` (web on :3000), `uvicorn` (api on :8000), local Postgres (brew, Postgres.app, or any cloud Postgres URL)
- **Production**: Vercel (web) + Railway (api + Postgres add-on)
- **Self-host**: fork → connect Vercel → connect Railway → set env vars → done

---

## 3. Backend (`apps/api`)

### Stack

- **Python 3.13**
- **uv** for package management
- **FastAPI 0.135.3**
- **Pydantic v2** for request/response schemas + settings
- **SQLAlchemy 2.0** async + **asyncpg** for Postgres
- **Alembic** for migrations
- **pandas 2.x + numpy + scipy** for analysis
- **structlog** for JSON logs
- **pytest + pytest-asyncio + httpx.AsyncClient** for tests
- **ruff** + **pyright** (strict mode)

### Module layout

```
apps/api/app/
├── main.py                    # FastAPI app, CORS, lifespan, routers
├── settings.py                # Pydantic Settings: DATABASE_URL, CORS_ORIGIN, MAX_UPLOAD_MB, SHARE_TTL_DAYS
├── routers/
│   ├── analyze.py             # POST /analyze
│   ├── share.py               # POST /share, GET /r/{id}
│   └── health.py              # GET /healthz
├── parsing/
│   ├── zip_loader.py          # Open zip, locate the 4 CSVs, validate
│   ├── csv_schema.py          # Expected columns per file (source of truth)
│   ├── frames.py              # Load CSVs → typed pandas DataFrames
│   └── errors.py              # ParseError hierarchy
├── analysis/
│   ├── metrics.py             # Aggregates: mean recovery, mean HRV, etc.
│   ├── trends.py              # Rolling windows, day-of-week, weekly aggregates
│   ├── sleep.py               # Sleep-specific computations (stages, debt, hypnogram)
│   ├── strain.py              # Strain, workouts, HR zones
│   ├── insights.py            # Insights engine — rules that produce Insight objects
│   └── pipeline.py            # Orchestrates: parsed frames → WhoopReport
├── models/
│   ├── report.py              # WhoopReport, DialMetric, TrendPoint, etc. (Pydantic)
│   ├── insight.py             # Insight, InsightSeverity
│   └── share.py               # ShareCreate, ShareResponse
├── db/
│   ├── base.py                # SQLAlchemy declarative base
│   ├── session.py             # Async session factory
│   └── models.py              # SharedReport ORM model
└── alembic/                   # Migrations
```

### The pipeline

```python
# analysis/pipeline.py
async def analyze_zip(file: UploadFile) -> WhoopReport:
    frames = parse_zip(file)                    # → ParsedFrames
    metrics = compute_metrics(frames)
    trends = compute_trends(frames)
    sleep = compute_sleep_breakdown(frames)
    strain = compute_strain_breakdown(frames)
    insights = run_insight_rules(frames, metrics, trends, sleep, strain)
    return WhoopReport(
        period=...,
        dials=...,
        metrics=metrics,
        recovery=...,
        sleep=sleep,
        strain=strain,
        workouts=... or None,
        journal=... or None,
        trends=trends,
        insights=insights,
    )
```

### Insights engine

Pure functions; each returns `Insight | None`. Insights with `None` are dropped from the response. Rules are easy to add and test in isolation.

```python
INSIGHT_RULES = [
    insight_undersleep,
    insight_bedtime_consistency,
    insight_late_chronotype,
    insight_overtraining,
    insight_sick_episodes,
    insight_travel_impact,
    insight_dow_pattern,
    insight_sleep_stage_quality,
    insight_long_term_trend,
    insight_workout_mix,
]
```

See §11 for the rule catalog (the 10 starter rules and what they detect).

### Endpoints

```
POST /analyze
  Body: multipart/form-data, file=<zip>
  Response: 200 WhoopReport (~100–300 KB JSON)
  Errors: 400, 413, 500 (see §6)

POST /share
  Body: { "report": <WhoopReport JSON> }
  Response: 201 { "id": "abc12345", "url": "/r/abc12345", "expires_at": "2026-05-07T..." }
  Errors: 400 (oversize), 422 (invalid shape)

GET /r/{id}
  Response: 200 WhoopReport, or 404 if expired/not found

GET /healthz
  Response: 200 { "ok": true, "db": "ok" }
```

### Storage schema (single table)

```sql
CREATE TABLE shared_reports (
  id          TEXT PRIMARY KEY,           -- nanoid, 8 chars
  report      JSONB NOT NULL,             -- the WhoopReport
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at  TIMESTAMPTZ NOT NULL        -- created_at + 30 days
);
CREATE INDEX idx_shared_reports_expires ON shared_reports(expires_at);
```

### Cleanup

Background task in FastAPI's `lifespan` runs every 6 hours:

```python
async def periodic_cleanup():
    while True:
        await asyncio.sleep(6 * 3600)
        async with session() as s:
            await s.execute(
                delete(SharedReport).where(SharedReport.expires_at < utcnow())
            )
            await s.commit()
```

No external CRON. Single Railway worker handles it; if we ever scale horizontally we move it to a separate scheduler.

### Limits

- Max upload: **50 MB** (Whoop exports rarely exceed 5 MB; 50 is generous)
- Max share JSON: **2 MB**
- CORS: only the configured Vercel origin + `localhost:3000` for dev

---

## 4. Frontend (`apps/web`)

### Stack

Already in the monorepo:
- **Next.js 16.2.2** (App Router; breaking changes — read `node_modules/next/dist/docs/` before coding)
- **React 19.2.4** + **React Compiler** (less manual `useMemo`)
- **Tailwind v4**
- **Biome 2.2** for lint/format
- **Bun**

To add:
- **echarts** + **echarts-for-react** — for the iconic dial (`gauge` series), trends, heatmap. Loaded via `dynamic(() => import(...), { ssr: false })` because ECharts touches `window`. Use `ReactEChartsCore` with manual module registration to keep bundle small.
- **react-dropzone** for upload UX
- **clsx** for conditional classes
- **nanoid** for client-side share-id display
- **next/font** with **Inter** (replacement for Whoop's Proxima Nova) + **JetBrains Mono** (replacement for DINPro on display numbers)

**No state management library** — URL state + a single React context for the in-memory report.

### Routes

```
/                   Landing — drag-and-drop upload, brief explainer, footer
/report             Local report (in-memory ReportContext)
/r/[id]             Shared report (Server Component fetches from API)
/about              How it works + WHOOP disclaimer + privacy statement
```

### Component structure

```
apps/web/src/
├── app/
│   ├── layout.tsx              # Root layout: fonts, theme, footer
│   ├── page.tsx                # Landing
│   ├── report/page.tsx         # /report (Client component)
│   ├── r/[id]/page.tsx         # /r/[id] (Server component)
│   └── about/page.tsx
├── components/
│   ├── upload/
│   │   ├── Dropzone.tsx
│   │   ├── UploadProgress.tsx
│   │   └── UploadError.tsx
│   ├── report/
│   │   ├── ReportShell.tsx     # Sidebar nav + main pane
│   │   ├── Sidebar.tsx
│   │   ├── ReportHeader.tsx    # Date range, share button
│   │   ├── DialCard.tsx        # Echarts gauge
│   │   ├── DialRow.tsx         # 3 dials side-by-side
│   │   ├── MetricCard.tsx
│   │   ├── InsightCard.tsx     # No left border
│   │   ├── TrendChart.tsx      # Echarts line
│   │   ├── DowBars.tsx
│   │   ├── Hypnogram.tsx
│   │   ├── HrZones.tsx
│   │   ├── WorkoutsList.tsx
│   │   └── ShareDialog.tsx
│   └── ui/                     # Tiny primitives: Button, Dialog, Tooltip
├── lib/
│   ├── api.ts                  # fetch wrappers
│   ├── types.ts                # Hand-written WhoopReport, Insight, etc.
│   ├── format.ts               # number/duration/date formatting
│   ├── colors.ts               # Whoop palette as JS constants
│   ├── errors.ts               # API code → friendly copy
│   └── echarts.ts              # Tree-shaken Echarts registration
├── context/
│   └── ReportContext.tsx
└── styles/
    └── globals.css             # Tailwind v4 + CSS custom properties for Whoop palette
```

### Colors live in two places (one source, two consumers)

1. **CSS custom properties** in `globals.css` → consumed by Tailwind v4 via `@theme` directive → `bg-card`, `text-rec-green`, `border-strain`, etc.
2. **TypeScript constants** in `lib/colors.ts` → consumed by ECharts options (which take JS objects, not CSS classes)

Both files are kept in sync manually; a small unit test asserts they don't drift.

### Upload UX

1. Landing page: huge drop zone with copy *"Drop your `my_whoop_data_*.zip`"*
2. On drop → POST `/analyze` → multi-stage progress: *"Uploading..." → "Parsing 4 files..." → "Computing insights..."* (visual stages tied to actual XHR upload progress + a deterministic ~500 ms hold during the analysis wait, for honesty)
3. On 200: stash JSON in `ReportContext`, `router.push('/report')`
4. On error: inline `<UploadError code={...} body={...}/>` with friendly copy + GitHub issue link

### `/report` route

- Reads from `ReportContext` (client component)
- If context empty (deep-link), redirect to `/`
- Renders `<ReportShell>` with sidebar + main pane
- Sidebar nav switches sections via React state, not navigation
- Sections: Overview, Recovery, Sleep, Strain, Trends, Workouts, Journal — Workouts/Journal entries hidden from sidebar if their data is empty/null

### `/r/[id]` route

- Server component, fetches from API at request time (`cache: 'no-store'` for now; could switch to `revalidate: 3600`)
- 404 → friendly "this report has expired or doesn't exist" page
- Renders the same `<ReportShell>`, only the data source differs
- Share button is **hidden** on this route — already shared

### Share dialog

- Click "Share" → modal: *"Your report will be saved for 30 days. Anyone with the link can view it. No personal info beyond the data you uploaded."*
- "Create link" → POST `/share` → show URL with copy button + success state

### Mobile

Responsive but not optimized. Sidebar collapses to a top tab bar at `<lg`. Dial row stacks. Hypnogram scrolls horizontally. Good enough for v1.

---

## 5. Data flow & API contract

### Happy path

```
Browser                                  API                          Postgres
   │                                       │                              │
   │  POST /analyze (multipart)            │                              │
   │──────────────────────────────────────►│                              │
   │                                       │ open zip → 4 CSVs            │
   │                                       │ pandas load + validate       │
   │                                       │ compute metrics + insights   │
   │                                       │ build WhoopReport JSON       │
   │◄──────────────────────────────────────│                              │
   │  200 { report }                       │                              │
   │  stash in ReportContext, push /report │                              │
   │  user explores                        │                              │
   │                                       │                              │
   │  POST /share { report }               │                              │
   │──────────────────────────────────────►│                              │
   │                                       │ generate nanoid              │
   │                                       │ INSERT shared_reports────────►│
   │◄──────────────────────────────────────│                              │
   │  201 { id, url, expires_at }          │                              │
   │  show copyable URL                    │                              │
                                                                          
   ... share opened by friend later ...
                                                                          
Friend's browser                       Vercel edge                     API
   │                                       │                              │
   │  GET /r/abc12345                      │                              │
   │──────────────────────────────────────►│                              │
   │                                       │ Server Component fetches:    │
   │                                       │  GET api/r/abc12345 ─────────►│
   │                                       │                          SELECT
   │                                       │◄─────── 200 { report }       │
   │◄──────────────────────────────────────│                              │
   │  fully rendered HTML+JSON             │                              │
```

### Type contract

Hand-written in `apps/web/src/lib/types.ts` and mirrored 1:1 by Pydantic v2 in `apps/api/app/models/`. Both sides own the contract; CI test asserts shape compatibility via a snapshot of one fixture report.

All `string` fields representing dates or times are **ISO 8601** (`"2026-04-07"` for date-only, `"2026-04-07T11:36:00Z"` for full timestamps in UTC). The exceptions are `avg_bedtime` / `avg_wake` (24-hour clock-only `"02:22"` for human display) and `bed_local` / `wake_local` in `BedtimeStrip` (same clock-only format).

```typescript
export type WhoopReport = {
  schema_version: 1;
  period: { start: string; end: string; days: number };
  dials: {
    sleep:    { value: number; unit: 'h'; performance_pct: number };
    recovery: { value: number; unit: '%'; green_pct: number };
    strain:   { value: number; unit: ''; label: 'light'|'moderate'|'high'|'all_out' };
  };
  metrics: {
    hrv_ms: number;
    rhr_bpm: number;
    resp_rpm: number;
    spo2_pct: number;
    sleep_efficiency_pct: number;
    sleep_consistency_pct: number;
    sleep_debt_min: number;
  };
  recovery: {
    trend: TrendPoint[];
    by_dow: DowEntry[];
    distribution: { green: number; yellow: number; red: number };
    sick_episodes: SickEpisode[];
  };
  sleep: {
    avg_bedtime: string;            // "02:22"
    avg_wake: string;               // "11:36"
    bedtime_std_h: number;
    avg_durations: { light_min: number; rem_min: number; deep_min: number; awake_min: number };
    stage_pct: { light: number; rem: number; deep: number };
    hypnogram_sample: HypnogramNight | null;
    consistency_strip: BedtimeStrip[];
  };
  strain: {
    avg_strain: number;
    distribution: { light: number; moderate: number; high: number; all_out: number };
    trend: TrendPoint[];
  };
  workouts: {
    total: number;
    by_activity: ActivityAgg[];
    top_strain_days: TopStrainDay[];
  } | null;
  journal: {
    days_logged: number;
    questions: JournalQuestionAgg[];
    note: string;
  } | null;
  trends: {
    monthly: MonthlyAgg[];
    first_vs_last_60d: TrendComparison;
  };
  insights: Insight[];
};

export type TrendPoint = { date: string; value: number | null };
export type DowEntry = { dow: 'mon'|'tue'|'wed'|'thu'|'fri'|'sat'|'sun'; mean: number; n: number };
export type SickEpisode = { date: string; recovery: number; rhr: number; hrv: number; skin_temp_c: number | null };
export type HypnogramNight = { start: string; end: string; segments: { stage: 'awake'|'light'|'rem'|'deep'; from: string; to: string }[] };
export type BedtimeStrip = { date: string; bed_local: string; wake_local: string };
export type ActivityAgg = { name: string; count: number; total_strain: number; total_min: number; pct_of_total_strain: number };
export type TopStrainDay = { date: string; day_strain: number; recovery: number; next_recovery: number | null };
export type JournalQuestionAgg = { question: string; yes: number; no: number; mean_rec_yes: number | null; mean_rec_no: number | null };
export type MonthlyAgg = { month: string; recovery: number; hrv: number; rhr: number; sleep_h: number };
export type TrendComparison = { bedtime_h: [number, number]; sleep_h: [number, number]; rhr: [number, number]; workouts: [number, number] };

export type Insight = {
  kind: 'undersleep'|'bedtime_consistency'|'late_chronotype'|'overtraining'|'sick_episodes'|'travel_impact'|'dow_pattern'|'sleep_stage_quality'|'long_term_trend'|'workout_mix';
  severity: 'low'|'medium'|'high';
  title: string;
  body: string;
  highlight: { value: string; unit?: string };
  evidence?: { value: number; label: string }[];
};

export type ShareCreateRequest = { report: WhoopReport };
export type ShareCreateResponse = { id: string; url: string; expires_at: string };
```

### Versioning

`schema_version: 1` in every report. Frontend can switch on it. Backend never re-reads stored reports — they're frozen JSON, the viewer just renders what's there. A v2 frontend must keep rendering v1 stored reports until they expire.

### Why one big JSON

- Stateless request → stateless response
- Largest field (recovery trend, ~400 daily points) is < 20 KB
- Sharing = freezing one JSON object. Trivial.

---

## 6. Error handling & validation

### Layer 1 — Upload boundary (FastAPI)

| Failure | HTTP | Body | Frontend handling |
|---|---|---|---|
| File > 50 MB | 413 | `{"code":"file_too_large","limit_mb":50}` | "File too large (max 50 MB)" |
| Not a zip | 400 | `{"code":"not_a_zip"}` | "That doesn't look like a Whoop export. We need a `.zip` file." |
| Zip is corrupted | 400 | `{"code":"corrupt_zip"}` | "Couldn't open the zip — it may be corrupted." |
| Missing `physiological_cycles.csv` | 400 | `{"code":"missing_required_file","file":"physiological_cycles.csv"}` | "Missing **physiological_cycles.csv**." + link to /about |
| Missing `sleeps.csv` | 400 | `{"code":"missing_required_file","file":"sleeps.csv"}` | Same |
| Columns don't match expected schema | 400 | `{"code":"unexpected_schema","file":"...","missing_cols":[...],"extra_cols":[...]}` | "Whoop changed their export format. Please open an issue." |
| `physiological_cycles.csv` empty after parse | 400 | `{"code":"no_data","file":"physiological_cycles.csv"}` | "We couldn't find any cycles in this export." |
| `workouts.csv` missing or empty | — | — | Workouts section hidden in sidebar |
| `journal_entries.csv` missing or empty | — | — | Journal section hidden in sidebar |
| Unhandled exception during analysis | 500 | `{"code":"analysis_failed","error_id":"<uuid>"}` | "Something went wrong. Open an issue with code `<uuid>`." Server logs full stack trace; user only sees the ID. |

**No PII in error responses.** Filenames are checked against an allowlist before being included.

**ZipBomb protection.** Uncompress with a hard cap on extracted size (200 MB total). Use `zipfile.ZipFile` with manual `read()` and a streaming counter, not `extractall()`.

### Layer 2 — Pure Python validation

A single source of truth in `parsing/csv_schema.py`. One Pydantic model per CSV listing required columns and dtypes. Parser:

1. Loads CSV with `pandas.read_csv(dtype=str)` (string-first to avoid silent coercion)
2. Validates columns against the schema
3. Coerces each column with explicit `pd.to_datetime` / `pd.to_numeric(errors='coerce')`
4. Drops rows where the timestamp is NaT
5. Drops fully-empty rows
6. Returns a typed `ParsedFrames` object

### Layer 3 — Analysis robustness

- Every `compute_*` function tolerates empty input (returns `None` or default with `n=0`)
- Insight rules return `None` if their statistical sample is too small (e.g., < 14 days)
- numpy warnings (mean of empty, divide by zero) are filtered explicitly per call, not globally

### Frontend errors

A single `<UploadError code body>` component that maps API codes to friendly messages from `lib/errors.ts`. Unrecognized codes fall back to the API's `body` text. **No retry button** for 4xx (user/format problems); **retry button** for 5xx only.

### Logging

- Backend: `structlog` JSON to stdout → Railway logs. One line per request: `request_id`, `endpoint`, `status`, `duration_ms`, `error_code`. No raw filenames or user data.
- Frontend: console only in dev. No third-party logging. No Sentry. (Privacy-first.)

---

## 7. Testing strategy

### Backend

| Layer | Tool | What we test |
|---|---|---|
| Parsing — schema | pytest | Each known-good column set passes; missing column raises specific error; wrong dtype coerces or fails predictably |
| Parsing — fixtures | pytest with real fixture zips | Happy zip (anonymized real export); 14-day minimal valid; no-workouts; no-journal; corrupt; wrong-format |
| Parsing — adversarial | pytest | Empty zip, zip with extra files (ignored), nested folder, ZipBomb (refused) |
| Analysis — metrics | pytest | Hand-built tiny DataFrames with known answers |
| Analysis — insights | pytest | Each rule with three inputs: triggers, doesn't trigger, edge case at threshold |
| Analysis — pipeline integration | pytest snapshot | Full `analyze_zip` on a fixture → snapshot WhoopReport JSON, compare to checked-in golden file |
| HTTP — endpoints | pytest + httpx.AsyncClient | `POST /analyze` happy + each error fixture; `POST /share` writes row + correct response; `GET /r/{id}` happy + 404 |
| DB — share lifecycle | pytest with disposable Postgres | Insert + read + expire (using `freezegun`); cleanup task removes only expired rows |

**Coverage target**: 90%+ on `analysis/`, `parsing/`, `routers/`. Don't chase 100%.

**Fixture zips** live in `apps/api/tests/fixtures/zips/` — small (a few hundred KB), checked into git. Either anonymized real exports or hand-crafted by a deterministic `tests/fixtures/build_fixtures.py` script.

**The most important test**: end-to-end snapshot of a real export → asserts the entire `WhoopReport` JSON matches a frozen snapshot. Catches accidental regressions cheaply.

### Frontend

| Layer | Tool | What we test |
|---|---|---|
| Type safety | TypeScript strict + Biome | Compile-time |
| Pure utility tests | Vitest | `lib/format.ts`, `lib/colors.ts`, `lib/errors.ts` |
| Component smoke tests | Vitest + @testing-library/react | `<DialCard>`, `<InsightCard>`, `<UploadError>` render expected output |
| No e2e in MVP | — | Add a single happy-path Playwright test in v1.1 once UI stabilizes |

**No visual regression / no Storybook in MVP.** YAGNI.

### CI

GitHub Actions, two jobs in parallel on every PR.

```yaml
# .github/workflows/ci.yml
name: ci
on: [pull_request, push]
jobs:
  api:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env: { POSTGRES_PASSWORD: postgres }
        ports: ['5432:5432']
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
        working-directory: apps/api
      - run: uv run ruff check
        working-directory: apps/api
      - run: uv run pyright
        working-directory: apps/api
      - run: uv run pytest -q --cov
        working-directory: apps/api
        env: { DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/postgres }
  web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v2
      - run: bun install
      - run: bun run lint
        working-directory: apps/web
      - run: bun run typecheck
        working-directory: apps/web
      - run: bun run test
        working-directory: apps/web
      - run: bun run build
        working-directory: apps/web
```

Both jobs must pass for merge. Branch protection on `main`. PR previews via Vercel for the web app; the API has no preview env (push-to-main on Railway).

---

## 8. Deployment & ops

### Production topology

```
                          ┌─────────────────────┐
   user ──── HTTPS ────►   │     Vercel          │
                          │  apps/web (Next 16) │
                          └──────────┬──────────┘
                                     │ HTTPS (CORS)
                                     ▼
                          ┌─────────────────────┐
                          │     Railway         │
                          │  apps/api (FastAPI) │
                          └──────────┬──────────┘
                                     │ DATABASE_URL
                                     ▼
                          ┌─────────────────────┐
                          │  Railway Postgres   │
                          └─────────────────────┘
```

### One-time setup

1. Push monorepo to GitHub (`whoop-lens` repo)
2. **Vercel**: connect repo → Root Directory = `apps/web` → env var `NEXT_PUBLIC_API_URL=https://api.whooplens.app` → deploy
3. **Railway**: new project → Deploy from GitHub → Root Directory = `apps/api` → add Postgres add-on → env vars `CORS_ORIGIN=https://whoop-lens.vercel.app`, `SHARE_TTL_DAYS=30`, `MAX_UPLOAD_MB=50`
4. Custom domain: `whooplens.app` → Vercel, `api.whooplens.app` → Railway; update `CORS_ORIGIN` accordingly

### `apps/api/railway.toml`

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2"
healthcheckPath = "/healthz"
healthcheckTimeout = 30
restartPolicyType = "always"
```

Nixpacks auto-detects Python from `pyproject.toml`. No Dockerfile.

### Migrations

Run on every deploy via `startCommand` (`alembic upgrade head &&`). Idempotent and safe.

### Env vars

| Key | Where | Notes |
|---|---|---|
| `DATABASE_URL` | Railway api | Auto-injected by Postgres add-on |
| `CORS_ORIGIN` | Railway api | Comma-separated origins |
| `MAX_UPLOAD_MB` | Railway api | Default 50 |
| `SHARE_TTL_DAYS` | Railway api | Default 30 |
| `LOG_LEVEL` | Railway api | Default `INFO` |
| `NEXT_PUBLIC_API_URL` | Vercel web | Public, baked into the build |

### Logging & observability

- Logs: structlog → stdout → Railway log viewer (free, 7-day retention)
- Metrics: Railway built-in CPU/RAM/request count
- Errors: Railway logs + the `error_id` users include in GitHub issues. No Sentry.
- Uptime: Railway healthcheck on `/healthz`. UptimeRobot can be added later if a public status page becomes useful.

### Rollback

One-click in Railway/Vercel deployments tabs. No manual procedure.

### Cost (rough)

- Vercel hobby: free
- Railway: ~$5–10/month for api + Postgres
- Domain: ~$10–15/year
- **Total: under $20/month** for the public hosted instance

### Self-hosting (README)

> 1. Fork this repo
> 2. Connect your fork to Vercel, set root = `apps/web`
> 3. Connect your fork to Railway, set root = `apps/api`, add Postgres add-on
> 4. Set `NEXT_PUBLIC_API_URL` on Vercel to your Railway API URL
> 5. Set `CORS_ORIGIN` on Railway to your Vercel URL
> 6. Done.

---

## 9. Conventions, naming, license

### Naming

- Display: **Whoop Lens**
- Slug: `whoop-lens`
- Wordmark in UI: `WHOOP·LENS` (uppercase, middot)
- Domain: `whooplens.app` (already configured)

### License

- **MIT** for code
- **CC BY 4.0** for design assets
- Whoop's own brand assets are referenced under fair use with explicit disclaimer; we never redistribute Whoop's logo or use the WHOOP wordmark in our UI

### Disclaimer

Footer on every page:
> *Whoop Lens is an independent open-source project. Not affiliated with, endorsed by, or sponsored by WHOOP, Inc. WHOOP is a trademark of WHOOP, Inc.*

Same statement on `/about` and at the top of `README.md`.

### Code style

| Language | Linter | Formatter | Type checker |
|---|---|---|---|
| TypeScript | Biome 2.2 | Biome 2.2 | tsc strict |
| Python | ruff | ruff format | pyright (strict on `app/`) |

### Git conventions

- Trunk-based: `main` is always deployable
- Branches: `feat/*`, `fix/*`, `chore/*`, `docs/*`
- Conventional commits: `feat(api): ...`, `fix(web): ...`
- PRs: small, focused, must pass CI, must include tests for new logic in `analysis/` or `parsing/`
- No force-push to `main`. No skipping hooks.

### Versioning

- API: `WhoopReport.schema_version = 1`. Bump only on breaking shape changes. Old shared reports keep rendering on the old schema.
- Releases: tag `v0.1.0` for MVP, semver thereafter.
- GitHub Releases with auto-generated changelogs.

### Repo files

```
~/projects/whoop-lens/
├── apps/
├── .github/
│   ├── workflows/ci.yml
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── CODEOWNERS
├── biome.json
├── package.json                # Bun workspaces root
├── README.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── LICENSE
└── docs/
    ├── architecture.md
    ├── insights.md
    └── whoop-format.md
```

---

## 10. Visual design system

All values below come from the official **WHOOP Brand & Design Guidelines PDF** (`developer.whoop.com`), confirmed by parallel research agents.

### Color palette

```css
/* CSS tokens — apps/web/src/styles/globals.css */
:root {
  /* Background */
  --bg-top:        #283339;
  --bg-bottom:     #101518;

  /* Surfaces */
  --card:          #1A2227;
  --card-alt:      #1F2A30;

  /* Text */
  --text:          #FFFFFF;
  --text-2:        rgba(255,255,255,0.72);
  --text-3:        rgba(255,255,255,0.48);

  /* Recovery zones (sharp boundaries — never interpolate) */
  --rec-green:     #16EC06;   /* 67–100% */
  --rec-yellow:    #FFDE00;   /* 34–66% */
  --rec-red:       #FF0026;   /* 0–33% */

  /* Neutral data lines (HRV, RHR trends) */
  --rec-blue:      #67AEE6;

  /* Strain & sleep */
  --strain:        #0093E7;
  --sleep:         #7BA1BB;   /* slate-blue, NOT purple */

  /* Accent / CTAs */
  --teal:          #00F19F;
}
```

The same constants live as JS in `apps/web/src/lib/colors.ts` for ECharts options.

### Typography

| Use | Whoop original | Our replacement | Notes |
|---|---|---|---|
| Headlines / body | Proxima Nova | **Inter** | Closest free match; load via `next/font` |
| Display numbers | DINPro Bold | **JetBrains Mono Bold** | Slightly more technical feel; tabular figures |
| Labels | Proxima Nova SemiBold UPPERCASE 0.18em letter-spacing | Inter same | Applied via Tailwind utilities |

### Layout grammar

- Dark mode by default (`linear-gradient(180deg, var(--bg-top), var(--bg-bottom))`)
- Cards: dark surface, **no border**, rounded `14px`, padding `16–20px`, separation via spacing not lines
- Whitespace 16–24px between cards
- No drop shadows, no card gradients
- Thin line icons (1.5–2 px stroke)
- Big display numbers, tiny uppercase low-opacity labels
- Color is reserved for meaning (recovery green/yellow/red, strain blue, sleep slate-blue) — chrome stays grayscale

### The dial component

The hero element. Uses ECharts `gauge` series with:
- Thick stroke (~10 px on a ~120 px dial)
- Single colored arc, unfilled portion at 8% white
- Centered display number with the JetBrains Mono font
- Tiny uppercase label below
- Sweep animation ~700 ms ease-out, number ticks in sync

### Sleep stages (hypnogram)

Tonal shades of `--sleep` (`#7BA1BB`), not multi-hue. Time-of-day x-axis (clock-based, not duration), stage stack y-axis (Awake top → Deep bottom).

### Recovery thresholds

```
0–33%   → red    (--rec-red)
34–66%  → yellow (--rec-yellow)
67–100% → green  (--rec-green)
```

Sharp boundaries — Whoop deliberately uses discrete colors, not a continuous gradient.

### Strain categories

```
0.0–9.9   → Light
10.0–13.9 → Moderate
14.0–17.9 → High
18.0–21.0 → All Out
```

Logarithmic scale; tick spacing on the dial is non-uniform.

---

## 11. Insights catalog (the 10 starter rules)

Each rule is a pure function in `analysis/insights.py`. Listed in the order they appear in the report (top = most impactful for the average user).

| # | Kind | Triggers when | Severity tiers |
|---|---|---|---|
| 1 | `undersleep` | ≥5% of nights are <6 h sleep | high if >15%, else medium |
| 2 | `bedtime_consistency` | 7-day rolling std of bedtime varies enough that low-var weeks score ≥5 pp better | medium |
| 3 | `late_chronotype` | Mean bedtime is after 01:00 AND within-7-9h-sleep windows show clear bedtime → recovery slope | informational |
| 4 | `overtraining` | Days with strain >15 are followed by recovery ≥5 pp lower than baseline | medium |
| 5 | `sick_episodes` | ≥1 day with HRV < 0.7×median AND RHR > 1.15×median AND recovery <30 | low (informational) |
| 6 | `travel_impact` | Any non-home timezone present, with measurable recovery delta | medium if ≥1 trip |
| 7 | `dow_pattern` | Worst day-of-week recovery is ≥5 pp below the best | low |
| 8 | `sleep_stage_quality` | Mean Deep% or REM% is above population norm (>20%) | informational |
| 9 | `long_term_trend` | First-60-day vs last-60-day comparison shows ≥3 metrics improving | informational |
| 10 | `workout_mix` | Walking + "Activity" account for >50% of total strain | informational |

Each rule has its own test file with three cases: triggers, does-not-trigger, edge-case-at-threshold. Adding a new rule = one function + one test + one entry in `INSIGHT_RULES`.

---

## 12. Implementation notes

These are not open questions — just things to be aware of during the build:

1. **Whoop empty-file behavior** — research suggests `workouts.csv` and `journal_entries.csv` are present-with-headers when empty rather than absent, but the parser handles both cases gracefully (file missing OR file with zero data rows is treated identically).
2. **Snapshot fixtures anonymization** — need a tiny `scripts/anonymize_export.py` that takes a real Whoop zip, drops timezones to a fixed offset, jitters timestamps by ±1 day, and outputs a checked-in fixture. Implementation detail for v1.
3. **Whoop Brand Guidelines updates** — the brand PDF on `developer.whoop.com` might be updated. Add a quarterly check in `CONTRIBUTING.md` to re-pull and confirm hex codes.

---

## Appendix A — Stack version pins

| Package | Version | Source |
|---|---|---|
| Next.js | 16.2.2 | already in `apps/web/package.json` |
| React | 19.2.4 | already in `apps/web/package.json` |
| Tailwind | v4 | already in `apps/web/package.json` |
| Biome | 2.2.0 | already in `apps/web/package.json` |
| ECharts | latest stable | to be added |
| echarts-for-react | latest stable | to be added |
| Python | 3.13 | new |
| FastAPI | 0.135.3 | confirmed by user |
| Pydantic | v2 (latest 2.x) | new |
| SQLAlchemy | 2.0 (latest) | new |
| asyncpg | latest | new |
| Alembic | latest | new |
| pandas | 2.x | new |
| numpy | latest | new |
| scipy | latest | new |
| pytest, httpx, freezegun, ruff, pyright | latest | new |

All versions verified for current maintenance status before being added; specific lockfile values to be set during implementation. Context7 was used to confirm FastAPI and `echarts-for-react` API surfaces; other libraries to be verified at the writing-plans stage.

---

## Appendix B — Research provenance

The visual design system in §10 was assembled by three parallel research agents who consulted:

- **WHOOP Brand & Design Guidelines (official PDF)** — `developer.whoop.com`
- WHOOP Developer Design Guidelines page
- WHOOP "All-New WHOOP Home Screen" announcement and 2025 product update articles
- WHOOP Support docs for Recovery, Sleep, Strain
- Bureau Oberhaeuser (the agency behind WHOOP's original visual language) Dribbble + Medium write-up
- DC Rainmaker WHOOP 4.0 / 5.0 reviews
- The5krunner WHOOP reviews
- WHOOP API developer docs for thresholds (recovery zones 67/34, strain category boundaries)

All hex codes are pulled directly from the official PDF, not from secondary aggregators.
