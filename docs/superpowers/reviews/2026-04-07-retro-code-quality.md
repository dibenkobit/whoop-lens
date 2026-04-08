# Retro code-quality review — hot modules

**Reviewer:** code-quality subagent
**Files reviewed:** insights.py, analyze.py, cleanup.py, pipeline.py (+ secondary: conftest.py, test_insights.py)
**Range:** 42efbe4..e313691
**Date:** 2026-04-07

## Summary

- Critical issues: 3
- Important issues: 5
- Minor issues: 6

## Strengths

- Error-code routing in `analyze.py` is complete: every `ParseError` subclass maps to the verbatim status/body documented in the plan, error-subclass handlers are listed before the generic `ParseError` catch, and the 500 branch emits an `error_id` (uuid4 hex) without echoing any internal detail or user filename — no PII leakage.
- `cleanup.py` is clean for shutdown: `periodic_cleanup()` swallows exceptions inside the loop so a transient DB outage doesn't kill the background task, and `app/main.py:lifespan` cancels + `suppress(CancelledError)` awaits the task on shutdown.
- The `delete_expired_now(session=...)` test seam is a sensible, minimal departure from the plan: the per-test `db_session` fixture rolls back so the test doesn't leave rows in the DB, and the production path (no session) still commits its own transaction via `async with SessionFactory()`.
- `pipeline.py` is a thin orchestrator — no business logic has leaked into it; section builders own their own null-handling, and `_compute_journal_section` correctly returns `None` for empty journals so the wire format drops the key.
- `parse_frames` always returns empty-with-columns DataFrames for missing workouts/journal files (never `None` or `KeyError`), which the insight rules correctly check with `f.workouts.empty` / `f.journal.empty`.
- The upload-size check in `analyze.py` rejects inside the chunked read loop before the full body is joined (64KB chunks), so a 51MB upload never becomes a 51MB bytestring in our process.
- `conftest.py` uses `NullPool` on the test engine, which is the right choice for the per-test SAVEPOINT-style rollback pattern used in `db_session`, and `os.environ.setdefault(...)` before the first `app.*` import avoids the Task-2 module-load-order footgun documented in HANDOFF §7 Lesson 3.
- `tests/analysis/test_insights.py` has 12 assertions, one per rule plus framework/list tests; the TDD loop was visibly followed and every rule has at least one happy-path trigger test.

## Issues

### Critical

#### C1. `insight_overtraining` crashes with `ValueError: cannot convert float NaN to integer` when a high-strain day is followed by a day with NaN recovery
**File:** `apps/api/app/analysis/insights.py:115-145`
**Problem:** The next-day recovery collection loop guards with `if v is not None` (line 126), which does **not** catch `float('nan')`. Pandas `df.loc[i, col]` returns NaN as `float('nan')`, not `None`. NaN recoveries are appended to `next_recoveries`, which makes `after = sum(...)/len(...)` NaN, which makes `delta = baseline - NaN = NaN`. The `if delta < 5` guard is always False for NaN (NaN comparisons return False), so the code falls through to `round(after)` / `round(delta)` — and `round(nan)` raises `ValueError`.

Reproduced empirically:
```python
f.cycles.loc[:, "Day Strain"] = 8.0
f.cycles.loc[:, "Recovery score %"] = 80.0
f.cycles.loc[0, "Day Strain"] = 16.0
f.cycles.loc[1, "Recovery score %"] = float("nan")  # a "missed" day
insight_overtraining(f)
# ValueError: cannot convert float NaN to integer
```
**Impact:** This will turn into a 500 on `POST /analyze` for any real user whose export contains a strenuous day followed by a day they didn't wear the strap (common — the fixture is synthetic, so the snapshot test never hits it). The existing `except Exception` in `analyze.py` catches it and returns `analysis_failed`, but the user sees a generic 500 instead of their report. This is a latent production bug that the happy-path snapshot test cannot catch.
**Fix:** Use pandas-aware NaN filtering:
```python
for i in high_strain_idx:
    if i + 1 < len(c):
        v = c.loc[i + 1, "Recovery score %"]
        if pd.notna(v):
            next_recoveries.append(float(v))
```
Add a regression test: `f.cycles.loc[1, "Recovery score %"] = float("nan")` after a high-strain day at index 0 and assert the rule still returns a valid `Insight` or `None`.

#### C2. `insight_bedtime_consistency` silently changed its trigger from the plan/spec and emits a nonsense `"+-60"` highlight
**File:** `apps/api/app/analysis/insights.py:55-91`
**Problem:** The committed code deviates from both the plan and spec §11:
- **Plan** gated triggering on `delta >= 5 and rec_low_var > 0 and rec_high_var > 0` (requiring both low-var and high-var weeks to exist AND a ≥5 pp delta between them).
- **Spec §11** defines the trigger as: *"7-day rolling std of bedtime varies enough that low-var weeks score ≥5 pp better."*
- **Implementation** changed the threshold buckets (high-var is now `> 2` instead of `> 3`), removed the `delta >= 5` gate entirely, and replaced it with `median_std >= 1.5`. It still computes `delta` but only uses it as the highlight value with a hardcoded `"+"` prefix.

The result is that if there are no rows in the low-variance bucket (`rec_low_raw` falls back to `0.0`), the rule emits `delta = 0 - 60 = -60` and the highlight becomes the string `"+-60"`. Reproduced:
```python
onsets = pd.to_datetime(["2025-01-01 23:00", "2025-01-02 03:00"] * 30 + ["..."])
f.cycles["Sleep onset"] = onsets[: len(f.cycles)]
f.cycles.loc[:, "Recovery score %"] = 60.0
# → highlight=InsightHighlight(value='+-60', unit='pp')
```
**Impact:**
1. Users see a malformed string (`"+-60pp"`) in a production card. This is a visible correctness bug, not a style bug.
2. The rule now fires for anyone with bedtime variance ≥1.5h **even if their recovery is not actually worse on irregular weeks** — which is the whole point of the insight. It silently became a "you have variable bedtime" rule rather than "variable bedtime hurts your recovery."
3. The body text says *"Your most stable weeks score much higher"* without ever verifying that they do.

This is the "silent behavior change" the HANDOFF §7 Lesson 1 warned about: spec review would check the title/kind match, and this change was never reviewed.

**Fix:** Restore the plan semantics, *and* guard against empty buckets and negative deltas:
```python
if rec_low_f == 0 or rec_high_f == 0:
    return None
delta = round(rec_low_f - rec_high_f)
if delta < 5:
    return None
# …
highlight=InsightHighlight(value=f"+{delta}", unit="pp"),
```
Add a regression test with uniformly-high recovery (`rec = 60`) that asserts the insight returns `None` (because delta is 0 or negative — the data doesn't prove the claim) instead of firing.

#### C3. `insight_undersleep` emits nonsense body text and `"+-N"` highlight when the user has no 8h+ nights
**File:** `apps/api/app/analysis/insights.py:18-52`
**Problem:** Same failure pattern as C2: when `rec[long_mask]` is empty (no 8h+ nights in the data), `rec_long_f` falls back to `0.0`, producing `delta = 0 - rec_short_f`. The hardcoded `f"+{delta}"` highlight then emits e.g. `"+-50"`, and the body text says *"on nights with 8+ hours it averages 0%"* — which is both factually wrong (we have no data for that bucket, not 0%) and will shock users. Reproduced:
```python
f.cycles.loc[:, "Asleep duration (min)"] = 300.0
f.cycles.loc[:, "Recovery score %"] = 50.0
# → body: "…on nights with 8+ hours it averages 0%…"
# → highlight: {'value': '+-50', 'unit': 'pp'}
```
**Impact:** This is the #1 rule in the insights catalog (top of the order in `INSIGHT_RULES`). Any user who consistently undersleeps — exactly the target of the rule — hits this bug. Their report card will show garbage text.
**Fix:** When the long-sleep bucket is empty, either (a) return `None` (sample too small to quantify the gap) or (b) skip the comparative statement. Minimum viable fix:
```python
if rec_long_f == 0.0:
    # We have no 8h+ nights to compare against — still fire but with a simpler body.
    delta_str = None
    body = (
        f"On nights under 6 hours your recovery averages {round(rec_short_f)}%. "
        f"Adding sleep is your single biggest lever."
    )
    highlight = InsightHighlight(value=f"{round(rec_short_f)}%")
else:
    delta = round(rec_long_f - rec_short_f)
    body = (...)  # as before
    highlight = InsightHighlight(value=f"+{delta}", unit="pp")
```
Or even simpler: require both buckets to be non-empty before firing. Add a regression test identical to the repro above and assert either `insight is None` or the body does not contain `"0%"`.

### Important

#### I1. Broken `rec_short_f == 0.0` / `rec_long_f == 0.0` fallback is structural, not local
**File:** `apps/api/app/analysis/insights.py:30-39, 71-80, 115-145, 175-199, 254-290, 293-321`
**Problem:** Six rules use the same pattern: `float(series.dropna().mean() or 0.0)` or an equivalent `if not isnan else 0.0`. The "or 0.0" fallback conflates "no data" with "recovery = 0%". When downstream arithmetic computes `delta = a - b`, a missing bucket silently produces an arbitrary-magnitude delta, which then:
- becomes a user-visible highlight (C2, C3),
- poisons `if delta < threshold` guards with misleading values,
- in `insight_long_term_trend` at line 254-290, could fire "trending in the right direction" for a user who has 120 days of data but zeros in key columns (RHR delta = `X - 0 = X`, sleep delta = `0 - 0 = 0`, rec delta = `X - 0 = X` → 2 "improvements" → trigger).

**Impact:** Structurally unsound — the fix is to propagate "missing" (return `None` or treat as "data too sparse") rather than substitute 0.0.
**Fix:** Replace `_safe_mean`-like defaults with explicit guards: if either side of a comparison is empty, return `None` from the rule. Consider a helper: `_pair_mean(rec, mask_a, mask_b) -> tuple[float, float] | None` that returns `None` when either bucket is empty.

#### I2. `periodic_cleanup` starts its first pass immediately on `lifespan_started`, runs inside the ASGI event loop with no backoff on failure
**File:** `apps/api/app/db/cleanup.py:37-44`
**Problem:** The loop runs `await delete_expired_now()` *before* the first `await asyncio.sleep(...)`. If the DB is briefly unreachable at startup (common on Railway during a rolling deploy or post-migration race), the first call logs `cleanup_failed` and then sleeps for 6 hours before retrying. The server is then "healthy" per `/healthz` but isn't pruning anything for 6 hours.
**Impact:** Low-frequency but real: a deploy that coincides with a 30-day-old batch of expired rows sees those rows linger for 6 hours. Not a data-safety issue but a quiet operational footgun.
**Fix:** Either (a) sleep *first* then run (so the first pass happens after the app is steady), or (b) on failure, sleep a short retry interval (e.g. 5 minutes) instead of the full 6 hours. Option (a) is simpler:
```python
async def periodic_cleanup() -> None:
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
        try:
            n = await delete_expired_now()
            log.info("cleanup_ran", deleted=n)
        except Exception:
            log.exception("cleanup_failed")
```

#### I3. `analyze.py` accepts the plan's "stream to memory" comment at face value, but Starlette has already spooled the whole body to a tempfile before the handler runs
**File:** `apps/api/app/routers/analyze.py:31-45`
**Problem:** The comment `# Stream into memory but enforce the cap` and the chunked read loop suggest the code rejects oversize uploads *before* they land in our process. In reality, by the time `analyze(file: UploadFile)` is called, Starlette has already spooled the entire request body to a `SpooledTemporaryFile` (default 1MB in-memory, rest on disk). Our loop then streams it back from that temp file. The actual protection against DoS is at the reverse-proxy level (Railway's request body limit), not here.

**Impact:** Not a security bug (Railway and the `MAX_UPLOAD_MB` cap work), but the comment is misleading and future maintainers may believe the check saves the server from memory exhaustion. If the app is ever self-hosted behind a proxy that doesn't cap request bodies, the spooling happens before our check.
**Fix:** Update the comment to reflect reality, e.g. `# Starlette already spooled the body; enforce our own cap before we hold the bytes in RAM.` Optionally add a note that reverse proxies are the first line of defense.

#### I4. `_compute_journal_section` hardcodes `mean_rec_yes` / `mean_rec_no` to `None`
**File:** `apps/api/app/analysis/pipeline.py:20-39`
**Problem:** Every journal question is emitted with `mean_rec_yes: None, mean_rec_no: None`. The `JournalQuestion` model at `app/models/report.py:168` declares `mean_rec_yes: float | None` — so it's wire-legal — but the whole point of the journal section is to correlate yes/no answers against next-day recovery. Returning `None` means the frontend will render empty/disabled cells indefinitely.
**Impact:** Not a bug relative to the plan (the plan code is the same), but it's a silent feature omission. The spec and plan don't explicitly require this join, so this is a design choice that should be confirmed or explicitly deferred. Flagging because "mean_rec_yes" as a field name implies it should contain a computed mean.
**Fix:** Either (a) implement the join against `f.cycles` recovery for the matching day (acceptable level of effort: ~10 lines), or (b) remove these fields from the wire contract to avoid raising frontend expectations. Pick one before the frontend build starts.

#### I5. `insight_travel_impact` counts NaN timezone rows as "away" days
**File:** `apps/api/app/analysis/insights.py:175-199`
**Problem:** `away_mask = c["Cycle timezone"] != home_tz` treats any row whose timezone is NaN/None as "not equal to home" (pandas `!=` returns True for NaN comparisons). If a user has ≥3 rows with NaN timezone, those are counted as travel days, inflating `away_mask.sum()` and distorting `rec_away`.
**Impact:** Spurious "Travel hits your recovery" insight for users who have a small number of missing-timezone rows (common for the first few days of a Whoop relationship).
**Fix:**
```python
tz_col = c["Cycle timezone"]
away_mask = tz_col.notna() & (tz_col != home_tz)
```
Add a regression test with mixed NaN/home/away timezones.

### Minor

#### M1. `insight_bedtime_consistency` body text names a hardcoded "7-day std" threshold of `round(median_std, 1)h` that is computed post-trigger
**File:** `apps/api/app/analysis/insights.py:86-89`
**Problem:** The body says *"Irregular bedtimes (7-day std {median_std}h) are linked to lower recovery"* — but the rule no longer verifies the "linked to lower recovery" claim (see C2). Even after C2 is fixed, the text is passive-aggressive about median_std without context.
**Fix:** Fold the numerical delta into the body once C2's trigger is restored, and drop the bare `median_std` figure.

#### M2. `insight_long_term_trend._mean` inner helper uses `or 0.0` fallback and is untyped on `df`
**File:** `apps/api/app/analysis/insights.py:261-262`
**Problem:** The `_mean` helper takes `df: pd.DataFrame` (typed) but the overall pattern is the same "zero = no data" footgun as I1. Less critical here because the rule requires ≥120 cycles, so all-NaN columns are very unusual in practice.
**Fix:** Same as I1 — return `None` from the rule if any of the three metrics has an empty bucket.

#### M3. `insight_sick_episodes` body text says "On these days HRV crashed" (plural) but the rule fires on n=1
**File:** `apps/api/app/analysis/insights.py:148-172`
**Problem:** The title correctly handles singular ("1 likely illness day"), but the body always uses plural ("On these days…"). Minor grammar nit.
**Fix:** `"On that day HRV crashed…"` when `n == 1`.

#### M4. `test_insight_overtraining_triggers` is tightly coupled to integer-position semantics of `cycles` ordering
**File:** `apps/api/tests/analysis/test_insights.py:81-92`
**Problem:** The test does `f.cycles.loc[:5, "Day Strain"] = 16.0` then `f.cycles.loc[1:6, "Recovery score %"] = 25.0` and relies on the happy fixture being already sorted by `Cycle start time`. The rule's `c = f.cycles.sort_values("Cycle start time").reset_index(drop=True)` re-sorts, so if the fixture ever stops being pre-sorted (or if the fixture seed changes the order), this test silently starts comparing the wrong rows. Not wrong today but brittle.
**Fix:** Build the test DataFrame explicitly rather than mutating the fixture, or add an explicit `sort_values` assertion after mutation.

#### M5. `delete_expired_now(session=...)` silently differs from production path: the session-provided branch flushes but never commits, while the production branch commits
**File:** `apps/api/app/db/cleanup.py:27-34`
**Problem:** The docstring says "caller manages the transaction" which is correct, but it's easy to misuse — a developer could pass a session expecting commit-on-return and the deletes would be rolled back. The `await session.flush()` is also redundant (the `execute(delete(...))` autoflushes).
**Fix:** Drop the redundant `flush()` and tighten the docstring: *"If **session** is provided, the caller MUST commit or rollback; this function never commits on a caller-provided session."*

#### M6. `conftest.py` has two functionally identical session-scoped `build_all_fixtures` fixtures (`_build_fixtures` in conftest, `_ensure_fixtures` in test_insights.py)
**File:** `apps/api/tests/conftest.py:35-37`, `apps/api/tests/analysis/test_insights.py:16-18`
**Problem:** Redundant — the conftest version already runs autouse at session scope, so the per-file one adds nothing. Harmless (idempotent) but confusing.
**Fix:** Delete the per-file `_ensure_fixtures` fixture; rely on the conftest version.

## Assessment

The hot modules are mostly in good shape — error routing, shutdown handling, and wire-format drop-none are all correct — but there are **three critical correctness bugs in `insights.py` that a real user's export will hit immediately**: `insight_overtraining` crashes on NaN next-day recovery (C1), and both `insight_undersleep` (C3) and `insight_bedtime_consistency` (C2) emit malformed `"+-N"` strings plus misleading body text when one of their comparison buckets is empty. The root cause is a shared anti-pattern — `float(series.mean() or 0.0)` — that conflates "no data" with "zero" across six rules (I1); fix that pattern once and at least half the insight-layer fragility goes away. C2 also documents a silent spec-deviating trigger change that slipped through batch mode and should be reverted to match spec §11. None of the other modules (`analyze.py`, `cleanup.py`, `pipeline.py`, `conftest.py`) have critical issues, though `cleanup.py` has a small operational wart around first-run timing (I2) and `analyze.py` has a misleading "streaming" comment (I3). Recommend blocking frontend build until C1-C3 are fixed and I1 is either addressed structurally or explicitly deferred with a tracking issue — otherwise the first real-user upload will either crash or show garbage text in the most prominent card on the report.
