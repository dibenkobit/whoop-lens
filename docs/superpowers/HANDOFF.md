# Handoff to next agent — Whoop Lens backend

**Date:** 2026-04-07
**Reason:** Previous agent ran out of context mid-execution; this is a complete handoff so a fresh agent can continue without re-discovering anything.

You are continuing **subagent-driven execution** of the Whoop Lens backend implementation plan. The first 3 of 22 tasks are complete and reviewed. Pick up at Task 4.

---

## 1. Project at a glance

- **Name:** Whoop Lens — open-source web app that takes a Whoop data export ZIP and returns a visual report styled after Whoop's design language.
- **Monorepo root:** `~/projects/whoop-lens` (= `/Users/dibenkobit/projects/whoop-lens`)
- **Layout:**
  - `apps/web/` — Next.js 16.2.2 + React 19 (already scaffolded by user, untouched by us)
  - `apps/api/` — FastAPI backend, currently being built (Tasks 1–22)
- **Branch:** `main` — the user **explicitly approved working directly on main** (fresh project, no in-flight work, trunk-based, frequent commits)
- **No remote yet** — local git only

---

## 2. The two source-of-truth documents

| Doc | Path |
|---|---|
| **Design spec** | `~/projects/whoop-lens/docs/superpowers/specs/2026-04-07-whoop-lens-design.md` |
| **Backend plan** (TDD task-by-task) | `~/projects/whoop-lens/docs/superpowers/plans/2026-04-07-whoop-lens-backend.md` |

The plan has **22 tasks**. Each task in the plan is self-contained: file paths, exact code blocks, exact commands, expected output, and a commit step. Read the plan task you're about to dispatch before writing the implementer prompt.

A **frontend plan** is intentionally not yet written — it's deferred until the backend ships.

---

## 3. What's done, what's next

| # | Task | Status | Commits |
|---|---|---|---|
| 1 | API skeleton with `uv init` | ✅ | `654ddd2` |
| 2 | Settings + structlog | ✅ | `13fc4fc` + fix `b16c1b4` |
| 3 | Pydantic models for WhoopReport contract | ✅ | `e12aa24` + fix `b165707` |
| **4** | **CSV schemas and parser errors** | **⏸ next** | — |
| 5 | Build deterministic fixture zips | ⏸ | — |
| 6 | ZIP loader | ⏸ | — |
| 7 | Frame parsing | ⏸ | — |
| 8 | Time helpers + base metrics | ⏸ | — |
| 9 | Trends + recovery section | ⏸ | — |
| 10 | Sleep section | ⏸ | — |
| 11 | Strain + workouts section | ⏸ | — |
| 12 | Insights framework + 3 sleep rules | ⏸ | — |
| 13 | Insights — overtraining/sick/travel | ⏸ | — |
| 14 | Insights — dow/stage/trend/mix | ⏸ | — |
| 15 | Pipeline + snapshot test | ⏸ | — |
| 16 | Database (SQLAlchemy + Alembic) | ⏸ | — |
| 17 | POST /share + GET /r/{id} | ⏸ | — |
| 18 | POST /analyze | ⏸ | — |
| 19 | /healthz + CORS + lifespan + cleanup | ⏸ | — |
| 20 | Final lint + type-check + suite | ⏸ | — |
| 21 | Railway deploy config | ⏸ | — |
| 22 | GitHub Actions CI | ⏸ | — |

**Verify:** `cd ~/projects/whoop-lens && git log --oneline -10` should show the 5 task commits above plus 4 doc commits below them. HEAD = `b165707`.

**Test status as of HEAD:** `cd ~/projects/whoop-lens/apps/api && uv run pytest -v` → 13 passed. `uv run pyright` → 0 errors.

---

## 4. Workflow you must follow

Use the **`superpowers:subagent-driven-development`** skill (the SKILL.md is at `/Users/dibenkobit/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/subagent-driven-development/`). Read it.

Per-task loop:

1. **Mark current task in_progress** in your task tracker (TaskCreate/TaskUpdate)
2. **Capture BASE_SHA** with `cd ~/projects/whoop-lens && git rev-parse HEAD`
3. **Dispatch implementer subagent** — `general-purpose` agent type, model `sonnet`. Paste the FULL task text from the plan into the prompt. Add the standard preamble (working dir, context, "TDD strict", "don't add extras"). See §6 for the prompt template.
4. **Wait for implementer report.** Capture HEAD_SHA = the new commit SHA they made.
5. **Dispatch spec compliance reviewer** — `general-purpose` agent type, model `sonnet`. Paste the verbatim required content from the plan and ask them to verify by reading the actual files + running tests themselves. Tell them: "Be skeptical. Don't trust the report." See §6 for template.
6. **If spec review fails:** dispatch implementer again with the specific issues to fix. Re-review.
7. **If spec review passes:** dispatch code quality reviewer — agent type `superpowers:code-reviewer`. Provide BASE_SHA..HEAD_SHA, what was implemented, and focus areas. See §6 for template.
8. **If code review finds Critical/Important issues:** dispatch implementer to fix them, then re-dispatch the code reviewer. Loop until approved.
9. **If code review approved:** mark task complete, move to next task.

**Critical:** spec compliance review comes BEFORE code quality review. If you swap the order, you waste cycles on quality issues that turn out to not even satisfy the spec.

**Don't fix code yourself.** Always dispatch a fix subagent. Context pollution otherwise.

---

## 5. Local environment (already set up)

### Postgres

A Docker container `whoop-lens-pg` is running with Postgres 16 on `localhost:5432`. Database `whoop_lens` exists. `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/whoop_lens`.

**Verify:** `docker ps --filter name=whoop-lens-pg`. If it's not running, restart:

```bash
docker rm -f whoop-lens-pg 2>/dev/null
docker run --name whoop-lens-pg -d \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=whoop_lens \
  -p 5432:5432 postgres:16
```

`apps/api/tests/conftest.py` already sets `os.environ.setdefault("DATABASE_URL", ...)` to this URL, so tests run without any extra env.

### Python toolchain

- `uv 0.10.4` at `/Users/dibenkobit/.local/bin/uv`
- Python 3.13 — installed via uv on first sync
- Working dir for all `uv run` commands: `~/projects/whoop-lens/apps/api`

### `.env` file

There is no `.env` file. `conftest.py` covers tests; for `uvicorn` runs you'd need to export `DATABASE_URL` first. Tasks 1–3 don't require it.

---

## 6. Subagent dispatch templates

### Implementer prompt (general-purpose, model sonnet)

```
You are implementing **Task N: <name>** from the Whoop Lens backend plan.

## Working Directory
/Users/dibenkobit/projects/whoop-lens/apps/api/. Run uv and pytest from there.

## Context
Whoop Lens is an open-source FastAPI backend that takes a Whoop data export
ZIP and computes a WhoopReport JSON. Tasks 1-N-1 are complete (commits ...).
Current state: <test count> tests passing, pyright 0 errors. You're working
on main (user approved, fresh project). Each task ends with one conventional
commit.

A local Postgres is running on localhost:5432, DATABASE_URL is wired through
tests/conftest.py — you don't need to set it.

This task <one-sentence summary>. The implementation must follow strict TDD:
write the failing test first, run it, then implement, then run again, then
commit.

## Task Description
<paste the FULL task section from the plan here, verbatim, including all
step blocks, code blocks, and commit message>

## Important Notes
1. Strict TDD — test first, see it fail, then implement.
2. Don't add anything beyond what the plan specifies. YAGNI.
3. <task-specific gotchas — see §8 below for known ones>
4. Run uv run pyright before committing — must be 0 errors.

## Reporting
When done, report:
- Status: DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT
- Files changed (paths)
- pytest output (full count)
- pyright output
- Commit SHA
- Self-review findings
- Concerns

Don't mark complete unless pytest is green AND pyright is clean AND a single
commit was made.
```

### Spec reviewer prompt (general-purpose, model sonnet)

```
You are reviewing whether an implementation matches its specification. Be
skeptical — read the actual code, do not trust the implementer's report.

## What Was Requested
<paste the full task section from the plan, including all the verbatim code
the implementer was supposed to write>

## What Implementer Claims
<paste the implementer's status report including the commit SHA they made>

## Your Job
1. Read every file at /Users/dibenkobit/projects/whoop-lens/apps/api/<paths>
   and compare verbatim to the plan content above.
2. Verify the commit exists with `git log --oneline -5` and matches the
   expected message prefix.
3. Run the tests yourself: cd /Users/dibenkobit/projects/whoop-lens/apps/api
   && uv run pytest -v && uv run pyright. Don't trust the report.
4. Check for missing requirements AND for unrequested extras. The spec is
   floor and ceiling.

## Reporting
✅ Spec compliant — every requirement satisfied, tests + pyright clean
❌ Issues found — itemize file:line, what's wrong, expected vs actual
```

### Code quality reviewer prompt (superpowers:code-reviewer)

```
Review the code quality of Task N from the Whoop Lens backend plan.

## What was implemented
<implementer's report, paraphrased>

## Plan/requirements
Task N from /Users/dibenkobit/projects/whoop-lens/docs/superpowers/plans/2026-04-07-whoop-lens-backend.md.
Read the relevant section. Spec at /Users/dibenkobit/projects/whoop-lens/docs/superpowers/specs/2026-04-07-whoop-lens-design.md.

## Diff range
- BASE_SHA: <previous commit>
- HEAD_SHA: <new commit>
- Repo: /Users/dibenkobit/projects/whoop-lens

## What to focus on
<task-specific concerns, e.g.: type strictness, test coverage,
file responsibilities, edge cases, wire-format correctness>

## Reporting
Strengths · Issues (Critical/Important/Minor) · Assessment.
```

---

## 7. Lessons learned from Tasks 1–3 (you must internalize these)

### Lesson 1: Spec review and code quality review catch different things

Spec review checks "does the code match the spec." Code quality review checks "does the code actually do the right thing in practice." **These are different.** Task 3 had three critical wire-format bugs that spec review missed entirely (because the spec text itself was wrong) — code quality review caught all three by empirically running `model_dump()`.

Always run BOTH reviews. Always do spec first, then quality.

### Lesson 2: Pydantic v2 wire-format gotchas (already fixed in Task 3, but the patterns matter for future tasks)

- `Field(alias="from")` only affects **input** validation. For **output** serialization, use `validation_alias=AliasChoices(...) , serialization_alias="from"`.
- Optional fields with `T | None = None` ship as `null` in JSON. If the TS contract uses `field?:` (optional), `null` is wrong — use `model_serializer(mode="wrap")` to drop None, OR restructure to discriminated unions.
- `pydantic-settings` JSON-decodes `list[str]` env vars before validators run. Use `Annotated[list[str], NoDecode]` from `pydantic_settings` (already applied in `app/settings.py`).

### Lesson 3: Module-level side effects break tests

`app/main.py` calls `get_settings()` at module load. Without `tests/conftest.py` setting a default `DATABASE_URL`, importing `app.main` from any test file would crash test collection. **Already fixed in Task 2.** When Tasks 17/18 add HTTP tests, this matters.

### Lesson 4: `getLevelName` is not deprecated in Python 3.13, but it's buggy

`getLevelName(level)` returns a string like `"Level INFO"` for unknown inputs instead of an int — which crashes `make_filtering_bound_logger`. Use `getLevelNamesMapping().get(level.upper(), logging.INFO)` instead. **Already applied** in `app/logging_config.py`.

### Lesson 5: `WriteLoggerFactory`, not `PrintLoggerFactory`

structlog warns against `PrintLoggerFactory` when stdlib also writes to stdout (as `logging.basicConfig` does), because `print()` is not atomic. Uvicorn access logs would interleave with our JSON. **Already applied** in `app/logging_config.py`.

### Lesson 6: Plan code blocks may have bugs

The plan was reviewed for placeholders and consistency, but the code blocks inside it weren't unit-tested before being committed. Tasks 1, 2, and 3 each surfaced 1–3 bugs in the plan code. Treat the plan as a strong starting point, **not** as known-good code. The implementer subagent should follow the plan but also notice when something doesn't compile or doesn't match the apparent intent.

### Lesson 7: When code review finds Critical issues, fix THIS task before moving on

Don't accumulate technical debt. If wire-format bugs ship to Task 4, the snapshot test in Task 15 will lock them in and they become much harder to remove. Fix-and-re-review is the right loop.

---

## 8. Known gotchas to mention in implementer prompts

When dispatching implementers for upcoming tasks, include the relevant gotcha in the prompt's "Important Notes" section:

**Tasks 4, 5 (parsing/csv_schema, fixtures):**
- Don't use `pandas.read_csv` defaults — string-first then explicit coerce. The plan specifies this.
- Fixture builder uses `random.Random(SEED)` (seed 42) — keep deterministic for snapshot tests later.
- `tests/fixtures/__init__.py` and `tests/parsing/__init__.py` must both exist (pyright excludes `tests/` so no type-check pressure).

**Tasks 6, 7 (zip_loader, frames):**
- Plan uses `dataclass(frozen=True)` for `LoadedZip` and `ParsedFrames` — keep that.
- Empty workouts/journal CSVs become empty `pd.DataFrame` with the right columns; **never None or KeyError**. The frontend will check `workouts is None` only at the report level.

**Tasks 8–11 (analysis):**
- Use `_safe_mean` helper or equivalent — don't crash on empty Series.
- All compute_* functions must tolerate empty input and return either a default object or `None`.
- `numpy` warnings filtered per call site, not globally (the plan specifies this).

**Tasks 12–14 (insights):**
- Each rule returns `Insight | None`. Returning None drops the insight from the response.
- Sample-size guards: most rules need at least 14 days of data.
- Tests use the `_happy_frames()` helper from `tests/analysis/test_insights.py`.

**Task 15 (pipeline + snapshot):**
- Snapshot test uses `pytest --snapshot-update` to regenerate. The first run creates the file; subsequent runs assert against it.
- The snapshot is a frozen JSON of the entire WhoopReport for the happy fixture. Keep it stable.

**Task 16 (DB):**
- Use `from app.db.session import engine` carefully — `engine` is created at module load and uses `get_settings().database_url`. Test fixtures use `_create_schema` (per-test rollback).
- Alembic file should be renamed to `0001_create_shared_reports.py` for stable ordering.

**Tasks 17, 18 (endpoints):**
- These use `httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test")`.
- The `_create_schema` fixture from `conftest.py` must be referenced as a parameter in HTTP test functions, even if unused, so pytest knows to wait for it.

**Task 19 (lifespan + cleanup):**
- Use `@asynccontextmanager` `lifespan` — the plan code is correct.
- `periodic_cleanup` sleeps for 6 hours; tests for it use `delete_expired_now()` directly with `freezegun`.

**Tasks 20–22 (lint, deploy, CI):**
- `uv run pyright` must be clean.
- `railway.toml` uses Nixpacks builder — no Dockerfile needed.
- CI workflow has a Postgres service; uses `astral-sh/setup-uv@v3`.

---

## 9. Things deliberately deferred (DO NOT reopen unless requested)

These came up in reviews and were intentionally not fixed:

- `extra="forbid"` on Pydantic models — too many models, low-value polish
- `tests/` in pyright include — currently excluded
- `log_level: Literal[...]` constraint on Settings
- Lifespan refactor of `main.py` (`get_settings()` at module load) — will be addressed naturally in Task 19
- More test coverage for Settings (whitespace CSV, MAX_UPLOAD_MB int parsing, empty CORS)
- `date` types instead of `str` for date fields
- `PostgresDsn` instead of `str` for DATABASE_URL

If a future reviewer flags any of these, dismiss with "deferred per HANDOFF.md §9."

---

## 10. User preferences and decisions

- **Language:** Russian conversation, English code/docs/UI
- **Tone:** Direct, concise, no preamble
- **Branch:** Direct on main, frequent commits, conventional commits (`feat(api):`, `fix(api):`, `chore(api):`, `docs:`)
- **Stack decisions** (already locked):
  - Backend: FastAPI 0.135.3, Pydantic v2, SQLAlchemy 2.0 async + asyncpg, Alembic, pandas, uv, ruff, pyright strict
  - Frontend: Next.js 16.2.2 + React 19 + Tailwind v4 + Bun + Biome + ECharts (not yet built)
  - Storage: Postgres on Railway
  - Deploy: Vercel (web) + Railway (api), no Docker, no compose
  - No auth, no LLM, no analytics, no tracking, no email
  - 30-day TTL on shared reports, lazy share (link only on user click)
  - Open source, MIT license, "Not affiliated with WHOOP, Inc." disclaimer
- **Specific call:** when this previous agent finished Task 3, the user asked to **stop before Task 4**. Then asked for this handoff. **Do not start Task 4 until the user explicitly says go.**

---

## 11. What to do first when you wake up

1. **Read this file end to end.**
2. **Read the plan** at `~/projects/whoop-lens/docs/superpowers/plans/2026-04-07-whoop-lens-backend.md` — at minimum skim Tasks 1–3 to understand the pattern, then read Task 4 in detail.
3. **Verify state:**
   ```bash
   cd ~/projects/whoop-lens && git log --oneline -10
   cd ~/projects/whoop-lens/apps/api && uv run pytest -v && uv run pyright
   docker ps --filter name=whoop-lens-pg
   ```
   Expected: HEAD `b165707`, 13 tests passing, pyright 0 errors, postgres container `Up`.
4. **Set up your task tracker** — use TaskCreate to make 19 entries (Tasks 4–22 from the plan). The previous agent's task IDs are not portable across sessions.
5. **Greet the user.** Tell them you're ready, you've read the handoff, you can confirm state is healthy, and you're waiting for their go-ahead to start Task 4. **Do not auto-start Task 4 — wait for explicit instruction.**

---

## 12. If anything is broken

**Postgres container missing:** see §5 for restart command.

**`uv sync` fails:** check `uv python list` for 3.13 — install if missing with `uv python install 3.13.12`.

**Tests fail unexpectedly:** check git log for any uncommitted changes (`git status -s`). The state should be clean at HEAD `b165707`. If not, ask the user before reverting.

**You're confused about a previous decision:** the **spec** and **plan** are the source of truth for "what to build." This file is the source of truth for "what was learned during execution and how to keep going." Re-read both.

**The code review subagent disagrees with the plan code:** the plan code is not gospel. If the subagent finds a real bug, fix it (see Lesson 6). Update the plan if the fix is substantive, but only with the user's blessing.

---

End of handoff. Good luck.
