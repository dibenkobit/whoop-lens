# Frontend execution handoff (mid-stream)

Picks up from the original handoff at `docs/superpowers/HANDOFF.md`. That document describes the overall workflow and lessons from the backend. This one is the delta: what's shipped so far in the frontend, where things stand, and exactly where to resume.

## Current state

- **HEAD:** `ee11175` (Task 9 implementer shipped; NOT yet reviewed)
- **Branch:** `main`. Local-only, no remote configured.
- **Tests:** 41 passing across 10 files.
- **Typecheck:** clean.
- **Lint (Biome):** 0 errors.
- **Build:** succeeds. `/` (landing), `/report`, `/_not-found` are the currently registered routes.
- **Backend dev server:** likely still running from the session start via `uvicorn app.main:app --port 8000` in the background with `DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:5432/whoop_lens'`. Verify with `curl -s http://localhost:8000/healthz`. If it's gone, restart with:
  ```bash
  cd /Users/dibenkobit/projects/whoop-lens/apps/api && \
    DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:5432/whoop_lens' \
    uv run uvicorn app.main:app --port 8000 > /tmp/whoop-lens-api.log 2>&1 &
  disown
  ```
- **Postgres:** container `whoop-lens-pg` running on `localhost:5432`. Verify with `docker ps --filter name=whoop-lens-pg`.

## Tasks shipped (1-8 fully, Task 9 implementer-only)

| # | Task | Commits | Notes |
|---|------|---------|-------|
| 1 | Dependencies, fonts, Whoop palette | `b2c73e7` | Intentional broken build until Task 4 |
| 2 | Hand-written types mirroring Pydantic | `491d837` | Wire-format gotchas verified (`from`, optional `unit`/`evidence`, discriminated dials) |
| 3 | Vitest + lib utilities | `0839721`, `2a2c7d7` | Fix-up: formatHours wrap, colors.test pin, apiBase trailing slash |
| 4 | Footer + Button + Dialog + Footer test | `122e164`, `4dac8d4` | Build first succeeds here. Cleanup commit: ghost button disabled state + Biome auto-fix on Task 3 files |
| 5 | Dial + DialRow (ECharts) | `2b7630a`, `798ac14` | Fix-up: use `recoveryColor()` helper, trim dead ECharts registrations |
| 6 | Landing page + Dropzone + upload flow | `8cf42b4`, `170e44a` | Fix-up: memoize Context value, wire `onDropRejected`, cancel timers on unmount |
| 7 | Report shell + sidebar + share dialog | `2a730dc`, `ca93a26` | Fix-up: AbortSignal on `createShare` (privacy fix!) + SectionErrorBoundary |
| 8 | Overview section | `3ec5bde`, `e65ec98` | Fix-up: sort top insight by severity (backend returns rule-order, not severity-order) |
| 9 | Recovery section | `ee11175` | Implementer-only. **Needs spec review → code-quality review → possible fix-up.** |

## Workflow rule recap (don't skip)

Per task (every task, every time):

1. **Read task in full from the plan** before dispatching.
2. Capture `BASE_SHA = git rev-parse HEAD`.
3. **Dispatch implementer** (general-purpose, sonnet). Paste the full task text + a context preamble. Warn about known plan defects (see "Recurring plan bugs" below).
4. **Dispatch spec reviewer** (general-purpose, sonnet). Independent verification against plan + Pydantic models.
5. **If spec fails** → fix subagent → re-dispatch spec reviewer. Don't skip.
6. **Dispatch code-quality reviewer** (`superpowers:code-reviewer`). Give it BASE_SHA..HEAD_SHA and explicit focus areas.
7. **If code review finds Critical/Important** → fix subagent → re-dispatch code-quality reviewer.
8. **Mark task complete in TaskList.**

**CRITICAL:** Spec review BEFORE code quality review. Don't skip either. **Don't fix code yourself — always dispatch a fix subagent.** Every time I considered "just editing directly" the reviewer caught a different real bug when I stuck to the subagent pattern.

## Where to resume — Task 9 is mid-loop

The Task 9 implementer reported DONE at HEAD `ee11175`. I had just finished reading their report when context was about to run out. The next two steps are:

### Step A: Spec review of Task 9

Dispatch the spec reviewer with this context:
- Commit under review: `ee11175`, parent `e65ec98`
- Plan section: `/Users/dibenkobit/projects/whoop-lens/docs/superpowers/plans/2026-04-07-whoop-lens-frontend.md` lines 2913-3273
- Two known implementer deviations (both pre-approved, apply same patterns as Task 5 and Task 8):
  1. `TrendLineChart.tsx` uses `echarts-for-react/lib/core` with `echarts={echarts}` prop (tree-shaking fix, mirrors Task 5 `Dial.tsx`)
  2. `RecoverySection.tsx` sorts `recoveryInsights` by severity via `toSorted` before `.slice(0, 2)` (mirrors Task 8 Overview fix)
- Verify `lib/echarts.ts` still has `LineChart`, `GridComponent`, `TooltipComponent`, `CanvasRenderer`, `GaugeChart` registered
- Verify the `/report/page.tsx` diff is minimal (just the `key === "recovery"` branch added)
- Null-safety spot-check: `SickEpisodesList` correctly uses `!== null` for `skin_temp_c` (which IS `| null` on the wire), NOT a truthy check (0°C is theoretically valid)
- Run tests, typecheck, lint, build yourself — confirm 41 passing, clean

### Step B: Code-quality review of Task 9

Use `superpowers:code-reviewer`. Diff range `e65ec98..ee11175`. Focus areas:
- Tree-shaking still works (`echarts-for-react/lib/core` usage)
- `TrendLineChart` re-builds option on every render (same concern as `Dial` — flag as Minor, don't fix)
- `DowBars` empty-state handling (`Math.max(..., 1)` guard against `Math.max()` returning `-Infinity`)
- `DowBars` `dim` threshold (`value < max * 0.7`) is visually meaningful only when `max` varies significantly — flag if it looks wrong
- Color contrast for `text-rec-yellow` on dark background (accessibility)
- `recoveryInsights.slice(0, 2)` — only 2 shown; the other filtered-out recovery insights are silently dropped. Acceptable per plan.
- `SickEpisodesList` uses `key={e.date}` — safe because episodes are unique by date
- Gradient fill color manipulation `${color}55` / `${color}00` in `TrendLineChart` assumes `color` is 6-digit hex; could break if someone passes rgba. Flag as Minor.

If review finds Important issues, dispatch a fix subagent in the same pattern as prior tasks.

## Remaining tasks: 10-18

Read each task in full before dispatching. File map of what each task creates is in the plan's §File map (lines 22-109) and in the task-specific `**Files:**` header.

| # | Task | Plan lines | Likely gotchas |
|---|------|------------|-----------------|
| 10 | Sleep section | 3277-3618 | **Hypnogram MUST handle `hypnogram_sample === null` gracefully** — backend v1 always returns null. Render friendly "not available" message. Pure-CSS hypnogram per plan (no ECharts). |
| 11 | Strain section | 3619-3750 | Uses StrainDial + distribution + trend. Probably another `TrendLineChart`. |
| 12 | Workouts section | 3751-3901 | **If `report.workouts === null`, the sidebar already hides it (Task 7). Task 12 still needs to handle the null case defensively in case the route renders via `/r/[id]` with workouts=null.** No per-workout HR zones in backend v1. |
| 13 | Trends section | 3902-4117 | Monthly heatmap + FirstVsLast comparison. Per the Task 5 review, `MonthlyHeatmap` is CSS-based in the plan, NOT ECharts. |
| 14 | Journal section | 4118-4241 | Hide if `report.journal === null`. Sidebar already does this. |
| 15 | /r/[id] shared route + not-found | 4242-4424 | **Server Component** (not Client). Uses `export const dynamic = "force-dynamic"`. `notFound()` from `next/navigation` triggers not-found.tsx. Passes `canShare={false}` to ReportShell (already plumbed in Task 7). |
| 16 | /about page | 4425-4516 | Static page. Disclaimer + how it works. |
| 17 | Env + next.config + deploy | 4517-4608 | **CSS hygiene cleanup opportunity.** See `docs/superpowers/reviews/frontend-deferred-for-task-17.md`. |
| 18 | GitHub Actions web job | 4609-end | **Add `web` job to existing `.github/workflows/ci.yml` — don't replace the file. Parallel to the existing `api` job.** |

## Recurring plan bugs (warn the implementer about these)

Every task so far has had 1-3 plan defects. Brief implementers about these patterns before dispatching:

1. **ECharts imports.** The plan keeps using `import("echarts-for-react")` (the default export) which pulls in the FULL echarts bundle. Always switch to `import("echarts-for-react/lib/core")` and pass `echarts={echarts}` as a prop. Task 5 and Task 9 both had this bug.
2. **Insight sorting.** Backend emits insights in rule registration order, NOT severity order. Any task that picks the "top N insights" must sort by severity first (`high → medium → low`). Task 8 and Task 9 both had this bug.
3. **Biome formatting.** The plan's code blocks often fail Biome's import-order, line-length, or trailing-comma rules. Implementers hit this and auto-fix. Don't flag as spec non-compliance.
4. **Privacy.** Whenever a component sends data to the backend (ShareDialog was the only one so far), verify: (a) only the derived report JSON is sent, not CSVs or filenames, (b) the fetch is cancellable via `AbortSignal` and actually aborted on user cancel/close/unmount.
5. **Null vs absent.** `Insight.highlight.unit` and `Insight.evidence` are OPTIONAL (`?:`) — use truthy checks (`unit ? ... : null`). `WhoopReport.workouts`, `journal`, `hypnogram_sample`, `SickEpisode.skin_temp_c` are `| null` — use `!== null`. Mixing these up is the most common wire-format bug.
6. **`setTimeout` lifetime management.** Tasks with any progress-staging or deferred work must cancel timers on unmount (`useEffect` cleanup) and on re-entry. Task 6 had this bug.
7. **Unstable Context values.** `<Context.Provider value={{...}}>` re-renders all consumers on every parent render. Wrap in `useMemo`. Task 6 had this bug.
8. **Missing defensive error boundaries.** Task 7 proactively added `SectionErrorBoundary` so a buggy section can't crash the whole report. Rely on that — don't add more boundaries.

## Deferred items tracker

`docs/superpowers/reviews/frontend-deferred-for-task-17.md` — CSS hygiene, deprecated expect-type APIs, non-critical polish. Don't carry these into tasks 10-16; they're for Task 17.

## User preferences (from original handoff)

- Language: **Russian** in conversation, **English** in code/docs/UI.
- Tone: direct, concise, no preamble, no trailing summaries.
- Commits: conventional, always `feat(web):` / `fix(web):` / `chore(web):` for frontend.
- Branch: direct on `main`, frequent commits.
- Status updates: brief, after every 2-3 tasks. Lead with green/red.
- Don't push to remote. None configured.
- Don't run `bun run dev` in the background. Waste of cycles.

## Things NOT to do

- **Don't batch tasks without review.** Backend Tasks 4-22 were batched and shipped 3 critical + 5 important bugs. Every frontend task with the full review loop has caught 1-3 issues before merge.
- **Don't fix code yourself.** Always dispatch a fix subagent. Every time I was tempted to just edit directly, a subagent found a different bug when I stuck to the pattern.
- **Don't reopen HANDOFF.md §9 deferred items** (extra="forbid", Literal log levels, date types over string types, Postgres DSN validation, tests/ in pyright include, lifespan refactor). Those are backend-side and still deferred.
- **Don't touch `apps/api/`.** Backend is done. Frontend is read-only against the models.
- **Don't invoke writing-plans or brainstorming.** The plan exists. Execute it.
- **Don't add features beyond the plan.** YAGNI. Every attempt to "improve" the plan's code has either been a bug (the plan's) or scope creep (mine).

## Specific instructions for the first few things you should do

1. Read this file end-to-end.
2. Verify state:
   ```bash
   cd /Users/dibenkobit/projects/whoop-lens && git log --oneline -10
   cd apps/web && bun run test 2>&1 | tail -5
   curl -s http://localhost:8000/healthz
   docker ps --filter name=whoop-lens-pg
   ```
3. Read Task 9 in the plan (lines 2913-3273).
4. Invoke `superpowers:subagent-driven-development` skill to get back into the workflow.
5. Dispatch the Task 9 spec reviewer using the context in "Step A" above.
6. Continue the loop.

Good luck. The workflow works — don't skip any of it.
