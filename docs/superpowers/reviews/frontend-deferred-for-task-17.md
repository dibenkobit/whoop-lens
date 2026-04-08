# Deferred items — to address in Task 17 (final polish)

These are findings from per-task code-quality reviews that the plan text specifies as-is (so deviating in their original task would break spec compliance) but should be revisited during the polish pass.

## From Task 11 review (d0c8066)

- **`StrainDistribution.tsx:32` width has no clamp.** `width: \`${value}%\`` accepts any `number` from the backend. Track has `overflow-hidden` so positive overflow is absorbed, but negatives would yield invalid CSS. Add `Math.max(0, Math.min(100, value))` if touched again.
- **`StrainSection.tsx:24` `replace("_", " ")` only replaces the first underscore.** Works for the current `"all_out"` label union but breaks silently on any future double-underscore variant. Use `.replaceAll("_", " ")` — same cost, future-proof.
- **`StrainDistribution` opacity tinting** lets the `bg-black/40` track bleed through on lower-tint rows. Pre-mixed colors via `color-mix` would give cleaner bars. Visual polish only.

## From Task 10 review (ae3e5ec)

- **`ConsistencyStrip` clamp inconsistency.** `apps/web/src/components/report/ConsistencyStrip.tsx:37-38` clamps `left` with `Math.max(leftPct, 0)` but uses the unclamped `leftPct` in `Math.min(widthPct, 100 - leftPct)`. For a bedtime before 18:00 (rare nap case) the bar visually overstates duration. Either widen `STRIP_START` or make the two clamps consistent.
- **`Hypnogram` is dead code in v1** because backend always returns `hypnogram_sample = null`. When backend ships per-night data, revisit:
  1. `Hypnogram.tsx:58` segment key `${seg.from}-${seg.stage}` collides on adjacent same-stage segments — add an index to the key.
  2. `Hypnogram.tsx:53` per-segment `width` has no `Math.max(..., 0)` guard for malformed `t1 < t0` data.
  3. `Hypnogram.tsx:42-54` row background labels ("Awake"/"REM"/...) are covered by segment bars when nights are fully populated — move the legend outside the plot area.
- **`SleepStageBreakdown.tsx:58` dead `|| 0` fallback.** `r.pct` is typed `number`; the `||` is dead code. Trivial cleanup.
- **`SleepStageBreakdown.tsx:37` `pct: 0` as in-band sentinel.** Using `0` to mean "hide bar and percentage" conflates a real value with a UI flag. A `showBar: false` field would be cleaner. Plan-faithful, deferred.
- **Filter array literal allocated per render** — same observation as Task 9 (`SleepSection.tsx:20-28`). Hoist to module scope as a `Set` if you ever care.

## From Task 9 review (ee11175)

- **`TrendLineChart` gradient hex assumption.** `${color}55` / `${color}00` at `apps/web/src/components/report/TrendLineChart.tsx:70-71` assumes `color` is a 6-digit hex string. Today the only caller passes `COLORS.recBlue` so it works, but the prop is typed `string`. A future caller passing `rgba(...)` or `#abc` would silently produce garbage. Either narrow the type, add a `withAlpha(hex, alpha)` helper, or accept the alpha separately.
- **`DowBars` `dim` threshold conflates "below relative best" with "low recovery."** `value < max * 0.7` at `apps/web/src/components/report/DowBars.tsx:28` dims a 70 bar in an all-green week and leaves all-red bars un-dimmed. Consider an absolute threshold (e.g. `< 50`) or drop the dim entirely and let `recoveryColor` carry the signal. Plan-faithful, so deferred.
- **`heightPct` is a no-op.** `(value / 100) * 100` at `apps/web/src/components/report/DowBars.tsx:26` simplifies to `value`. Trivial cleanup.

## From Task 1 review (b2c73e7)

- **CSS hygiene — duplicate `min-height` source of truth.** `globals.css` sets `html, body { min-height: 100vh }` while `layout.tsx` sets `<body className="min-h-screen ...">`. Pick one. Recommended: drop CSS rule, keep `min-h-screen` (or `min-h-dvh` for mobile).
- **CSS hygiene — gradient on both `html` and `body`.** Currently double-painted. Move to one selector with `background-attachment: fixed` for safety.
- **`-webkit-font-smoothing` duplicated** between `globals.css` body rule and the `antialiased` className on `<html>`. Drop one.
- **`font-feature-settings: "cv11", "ss01"` is Inter-specific** and inherits to JetBrains Mono. Scope to sans-only or remove and re-add per-component.
- **Token name collision risk:** `--color-text-2` / `--color-text-3` produce confusing utilities (`text-text-2`). Consider `--color-text-secondary` / `--color-text-muted` if any rename pass happens. (Low priority — touching this means rewriting every component className.)
- **`subsets: ["latin"]`** in `next/font` won't cover non-Latin journal entries. Consider `latin-ext` once Task 14 (JournalSection) is in place.
- **No `viewport` export** in `layout.tsx`. Add `themeColor: "#101518"` for dark mobile chrome.

## Notes for upcoming tasks (not deferred — apply in their own task)

- **Task 3 carry-forward (from Task 2 review):**
  1. In `tests/lib/types.test.ts`, replace `expectTypeOf(...).toMatchTypeOf<T>()` with `.toExtend<T>()` (the former is deprecated in expect-type ≥1.2.0, vendored by Vitest 4).
  2. Add a test that pins `HypnogramSegment.from` as the wire key — include a `@ts-expect-error` line on a `from_` variant so any future "fix" breaks compilation.
  3. In `lib/errors.ts` (created in Task 3), narrow `ApiErrorBody.code` to a literal union derived from the actual backend error codes (read `apps/api/app/routers/analyze.py` to enumerate). Consider replacing the current open shape `{ code: string; [key: string]: unknown }` with a discriminated union — keeps narrowing in the switch ergonomic and prevents typo bugs (`body.codee` is currently `unknown` instead of an error).
- **Task 4 risk (from Task 3 review): `@vitejs/plugin-react` is NOT installed.** Vitest 4's default loader can transform TSX, but `Footer.test.tsx` will import a component that imports `next/link`. Next 16's `next/link` may rely on RSC-aware bundling that Vite doesn't understand without a plugin. Task 4 implementer must verify component tests can render before writing the test body. If the test fails to compile, install `@vitejs/plugin-react` and add `react()` to `vitest.config.ts` plugins.
- **Task 4: `cn` helper.** If a `cn` helper is created, decide whether to add `tailwind-merge`. Current plan installs `clsx` only. Document the decision.
- **Task 4 cleanup opportunity:** `apps/web/package.json` has BOTH `jsdom@29` and `happy-dom@20` as devDependencies (Task 1 installed both as a hedge). `vitest.config.ts` uses `jsdom`. Pick one and remove the other once Task 4's component tests prove out the choice.
- **Task 5: `echarts-for-react` is "quiet" upstream.** Plan already mitigates with manual ECharts registration via `lib/echarts.ts` (tree-shake). If Strict Mode double-init issues appear, fall back to direct `echarts.init` in a `useEffect`.
