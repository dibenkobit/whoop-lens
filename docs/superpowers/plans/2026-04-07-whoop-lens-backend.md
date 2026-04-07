# Whoop Lens Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the FastAPI backend that accepts a Whoop data export ZIP, computes a `WhoopReport` JSON, supports lazy share links with 30-day TTL, and deploys to Railway with full test coverage.

**Architecture:** Three concerns, each its own package: `parsing/` (zip → typed pandas DataFrames), `analysis/` (DataFrames → `WhoopReport` Pydantic model), `routers/` + `db/` (HTTP endpoints + Postgres for shared reports). Strict TDD throughout — failing test → minimal implementation → passing test → commit.

**Tech Stack:** Python 3.13 · uv · FastAPI 0.135.3 · Pydantic v2 · SQLAlchemy 2.0 async · asyncpg · Alembic · pandas 2.x · numpy · scipy · structlog · pytest + pytest-asyncio + httpx + freezegun · ruff · pyright.

**Reference spec:** `docs/superpowers/specs/2026-04-07-whoop-lens-design.md` — re-read sections §3, §5, §6, §7, §8, §10 (palette/thresholds), §11 (insight rules) before starting.

---

## File map

```
apps/api/
├── pyproject.toml
├── uv.lock                              # generated
├── alembic.ini
├── railway.toml
├── .python-version
├── .gitignore                           # api-specific
├── README.md                            # one-paragraph "what is this"
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI app, CORS, lifespan, router includes
│   ├── settings.py                      # Pydantic Settings
│   ├── logging_config.py                # structlog setup
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── analyze.py                   # POST /analyze
│   │   ├── share.py                     # POST /share, GET /r/{id}
│   │   └── health.py                    # GET /healthz
│   ├── parsing/
│   │   ├── __init__.py
│   │   ├── errors.py                    # ParseError + subclasses
│   │   ├── csv_schema.py                # Required column lists for the 4 CSVs
│   │   ├── zip_loader.py                # Open zip, locate files, validate
│   │   └── frames.py                    # Coerce CSVs → ParsedFrames dataclass
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── time_helpers.py              # bedtime hour math, dow names, etc.
│   │   ├── metrics.py                   # Top-level aggregates
│   │   ├── trends.py                    # Rolling, dow, monthly
│   │   ├── sleep.py                     # Sleep stages, hypnogram, consistency strip
│   │   ├── strain.py                    # Strain, workouts, top strain days
│   │   ├── insights.py                  # 10 rules + INSIGHT_RULES list
│   │   └── pipeline.py                  # Orchestrates parsed → WhoopReport
│   ├── models/
│   │   ├── __init__.py
│   │   ├── report.py                    # WhoopReport + nested Pydantic models
│   │   ├── insight.py                   # Insight, InsightSeverity, InsightKind
│   │   └── share.py                     # ShareCreateRequest, ShareCreateResponse
│   └── db/
│       ├── __init__.py
│       ├── base.py                      # SQLAlchemy declarative base
│       ├── session.py                   # async_sessionmaker, get_session dep
│       ├── models.py                    # SharedReport ORM
│       └── cleanup.py                   # periodic_cleanup task
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_create_shared_reports.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py                      # pytest fixtures (DB session, app, client)
│   ├── fixtures/
│   │   ├── __init__.py
│   │   ├── build_fixtures.py            # Generates fixture zips deterministically
│   │   └── zips/
│   │       ├── happy.zip                # Synthetic 60-day complete export
│   │       ├── minimal_14d.zip          # 14-day valid export
│   │       ├── no_workouts.zip          # Cycles + sleeps + empty workouts/journal
│   │       ├── no_journal.zip           # Cycles + sleeps + workouts + empty journal
│   │       ├── corrupt.zip              # Truncated bytes, invalid central directory
│   │       └── wrong_format.zip         # Cycles CSV with renamed columns
│   ├── snapshots/
│   │   └── happy_report.json            # Expected output of pipeline on happy.zip
│   ├── parsing/
│   │   ├── test_zip_loader.py
│   │   ├── test_csv_schema.py
│   │   └── test_frames.py
│   ├── analysis/
│   │   ├── test_time_helpers.py
│   │   ├── test_metrics.py
│   │   ├── test_trends.py
│   │   ├── test_sleep.py
│   │   ├── test_strain.py
│   │   ├── test_insights.py
│   │   └── test_pipeline.py
│   └── routers/
│       ├── test_analyze.py
│       ├── test_share.py
│       └── test_health.py
└── scripts/
    └── anonymize_export.py              # Optional: real export → anonymized fixture
```

**Working directory for all commands:** `~/projects/whoop-lens/apps/api` unless noted otherwise.

---

## Task 0: Workspace prerequisites

**Files:** none yet — environment check only.

- [ ] **Step 1: Verify uv and Python 3.13 are available**

```bash
cd ~/projects/whoop-lens
uv --version
uv python list | grep "3.13"
```

Expected: uv >= 0.10, at least one `cpython-3.13.x` line. If 3.13 shows `<download available>`, run `uv python install 3.13.12`.

- [ ] **Step 2: Verify a Postgres is reachable for tests**

You need a Postgres instance for local test runs. Pick one:
- macOS: `brew install postgresql@16 && brew services start postgresql@16`
- Postgres.app
- A Railway dev branch (cheapest if you don't want a local install)

```bash
psql "$DATABASE_URL" -c 'select 1;' 2>&1 || echo "set DATABASE_URL first"
```

Expected: `1` printed, or set `DATABASE_URL=postgresql://localhost/postgres` and try again.

- [ ] **Step 3: Confirm root monorepo is clean**

```bash
cd ~/projects/whoop-lens
git status
```

Expected: `nothing to commit, working tree clean` (or only the design doc commit).

---

## Task 1: API skeleton with `uv init`

**Files:**
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/.python-version`
- Create: `apps/api/.gitignore`
- Create: `apps/api/README.md`
- Create: `apps/api/app/__init__.py`
- Create: `apps/api/app/main.py`
- Create: `apps/api/tests/__init__.py`
- Create: `apps/api/tests/test_smoke.py`

- [ ] **Step 1: Initialize the package with uv**

```bash
cd ~/projects/whoop-lens
mkdir -p apps/api
cd apps/api
uv init --package --name whoop-lens-api --python 3.13 .
```

This creates `pyproject.toml`, `.python-version`, `README.md`, and an `app/` directory with a placeholder. Delete the placeholder it generated:

```bash
rm -rf src
mkdir -p app tests
touch app/__init__.py tests/__init__.py
```

- [ ] **Step 2: Add core dependencies**

```bash
uv add "fastapi==0.135.3" "uvicorn[standard]" "pydantic>=2.7" "pydantic-settings>=2.4" "structlog>=24.1"
uv add --dev "pytest>=8.3" "pytest-asyncio>=0.24" "httpx>=0.27" "ruff>=0.6" "pyright>=1.1"
```

- [ ] **Step 3: Replace `pyproject.toml` with the canonical config**

Open `apps/api/pyproject.toml` and overwrite with:

```toml
[project]
name = "whoop-lens-api"
version = "0.1.0"
description = "Whoop Lens backend — analyze Whoop data exports"
requires-python = ">=3.13,<3.14"
dependencies = [
    "fastapi==0.135.3",
    "uvicorn[standard]>=0.32",
    "pydantic>=2.7",
    "pydantic-settings>=2.4",
    "structlog>=24.1",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "httpx>=0.27",
    "ruff>=0.6",
    "pyright>=1.1",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["app"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
filterwarnings = [
    "error",
    "ignore::DeprecationWarning",
]

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "RUF"]

[tool.pyright]
pythonVersion = "3.13"
typeCheckingMode = "strict"
include = ["app"]
exclude = ["tests"]
```

Then sync:

```bash
uv sync
```

- [ ] **Step 4: Add a `.gitignore`**

Create `apps/api/.gitignore`:

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.pyright/
*.egg-info/
htmlcov/
.coverage
dist/
build/
```

- [ ] **Step 5: Write the smoke test**

Create `apps/api/tests/test_smoke.py`:

```python
def test_truth():
    assert 1 + 1 == 2
```

Run it:

```bash
uv run pytest tests/test_smoke.py -v
```

Expected: `1 passed`.

- [ ] **Step 6: Write the FastAPI hello-world**

Create `apps/api/app/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="Whoop Lens API", version="0.1.0")


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "whoop-lens-api", "version": "0.1.0"}
```

Run the dev server in another terminal:

```bash
uv run uvicorn app.main:app --reload
```

In a third terminal:

```bash
curl -s http://localhost:8000/ | grep whoop-lens-api
```

Expected: a line containing `"name":"whoop-lens-api"`. Stop the server with Ctrl-C.

- [ ] **Step 7: Update `README.md`**

Overwrite `apps/api/README.md`:

```markdown
# whoop-lens-api

FastAPI backend for [Whoop Lens](https://whooplens.app). Accepts a Whoop data
export ZIP and returns a computed report. See `../docs/superpowers/specs/`.

## Dev

```bash
uv sync
uv run uvicorn app.main:app --reload
uv run pytest
```
```

- [ ] **Step 8: Commit**

```bash
cd ~/projects/whoop-lens
git add apps/api/
git commit -m "feat(api): scaffold FastAPI project with uv

- pyproject.toml with FastAPI 0.135.3 + Pydantic v2 + structlog
- pytest + ruff + pyright dev deps
- root health route returning name+version
- smoke test passing"
```

---

## Task 2: Settings and structured logging

**Files:**
- Create: `apps/api/app/settings.py`
- Create: `apps/api/app/logging_config.py`
- Modify: `apps/api/app/main.py`
- Create: `apps/api/tests/test_settings.py`

- [ ] **Step 1: Write the failing settings test**

Create `apps/api/tests/test_settings.py`:

```python
import pytest
from pydantic import ValidationError

from app.settings import Settings


def test_settings_loads_with_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost/test")
    s = Settings()
    assert s.max_upload_mb == 50
    assert s.share_ttl_days == 30
    assert s.log_level == "INFO"
    assert s.cors_origin == ["http://localhost:3000"]


def test_settings_parses_csv_cors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost/test")
    monkeypatch.setenv("CORS_ORIGIN", "https://a.com,https://b.com")
    s = Settings()
    assert s.cors_origin == ["https://a.com", "https://b.com"]


def test_settings_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings()
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
uv run pytest tests/test_settings.py -v
```

Expected: `ImportError` / `ModuleNotFoundError: No module named 'app.settings'`.

- [ ] **Step 3: Implement `settings.py`**

Create `apps/api/app/settings.py`:

```python
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(..., alias="DATABASE_URL")
    cors_origin: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        alias="CORS_ORIGIN",
    )
    max_upload_mb: int = Field(default=50, alias="MAX_UPLOAD_MB")
    share_ttl_days: int = Field(default=30, alias="SHARE_TTL_DAYS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("cors_origin", mode="before")
    @classmethod
    def split_cors(cls, v: object) -> object:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
uv run pytest tests/test_settings.py -v
```

Expected: `3 passed`.

- [ ] **Step 5: Implement structured logging**

Create `apps/api/app/logging_config.py`:

```python
import logging
import sys

import structlog


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(level)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)  # type: ignore[no-any-return]
```

- [ ] **Step 6: Wire settings + logging into main.py**

Replace `apps/api/app/main.py`:

```python
from fastapi import FastAPI

from app.logging_config import configure_logging, get_logger
from app.settings import get_settings

settings = get_settings()
configure_logging(level=settings.log_level)
log = get_logger(__name__)

app = FastAPI(title="Whoop Lens API", version="0.1.0")


@app.get("/")
def root() -> dict[str, str]:
    log.info("root_called")
    return {"name": "whoop-lens-api", "version": "0.1.0"}
```

- [ ] **Step 7: Run all tests**

```bash
uv run pytest -v
```

Expected: 4 passed (smoke + 3 settings).

- [ ] **Step 8: Commit**

```bash
git add apps/api/
git commit -m "feat(api): add Pydantic Settings and structlog

- Settings reads DATABASE_URL/CORS_ORIGIN/MAX_UPLOAD_MB/SHARE_TTL_DAYS/LOG_LEVEL
- CORS list parsed from comma-separated env var
- structlog configured with JSON renderer to stdout
- 3 settings tests passing"
```

---

## Task 3: Pydantic models for the report contract

**Files:**
- Create: `apps/api/app/models/__init__.py`
- Create: `apps/api/app/models/insight.py`
- Create: `apps/api/app/models/report.py`
- Create: `apps/api/app/models/share.py`
- Create: `apps/api/tests/test_models.py`

- [ ] **Step 1: Write a model round-trip test**

Create `apps/api/tests/test_models.py`:

```python
from datetime import datetime, timezone

from app.models.insight import Insight
from app.models.report import (
    DialMetric,
    Dials,
    Metrics,
    Period,
    RecoverySection,
    SleepSection,
    StrainSection,
    TrendsSection,
    TrendComparison,
    WhoopReport,
)
from app.models.share import ShareCreateRequest, ShareCreateResponse


def _minimal_report() -> WhoopReport:
    return WhoopReport(
        schema_version=1,
        period=Period(start="2025-01-01", end="2025-01-31", days=31),
        dials=Dials(
            sleep=DialMetric(value=8.0, unit="h", performance_pct=85.0),
            recovery=DialMetric(value=70.0, unit="%", green_pct=60.0),
            strain=DialMetric(value=10.0, unit="", label="moderate"),
        ),
        metrics=Metrics(
            hrv_ms=120.0,
            rhr_bpm=50.0,
            resp_rpm=15.0,
            spo2_pct=95.0,
            sleep_efficiency_pct=92.0,
            sleep_consistency_pct=60.0,
            sleep_debt_min=20.0,
        ),
        recovery=RecoverySection(
            trend=[],
            by_dow=[],
            distribution={"green": 60.0, "yellow": 35.0, "red": 5.0},
            sick_episodes=[],
        ),
        sleep=SleepSection(
            avg_bedtime="02:22",
            avg_wake="11:36",
            bedtime_std_h=1.5,
            avg_durations={"light_min": 270.0, "rem_min": 110.0, "deep_min": 100.0, "awake_min": 38.0},
            stage_pct={"light": 56.0, "rem": 22.0, "deep": 22.0},
            hypnogram_sample=None,
            consistency_strip=[],
        ),
        strain=StrainSection(
            avg_strain=10.0,
            distribution={"light": 50.0, "moderate": 40.0, "high": 9.0, "all_out": 1.0},
            trend=[],
        ),
        workouts=None,
        journal=None,
        trends=TrendsSection(
            monthly=[],
            first_vs_last_60d=TrendComparison(
                bedtime_h=(26.5, 25.5),
                sleep_h=(7.5, 8.0),
                rhr=(52.0, 50.0),
                workouts=(15, 30),
            ),
        ),
        insights=[],
    )


def test_report_round_trip() -> None:
    report = _minimal_report()
    data = report.model_dump(mode="json")
    again = WhoopReport.model_validate(data)
    assert again == report


def test_insight_kind_must_be_valid() -> None:
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Insight(
            kind="not_a_real_kind",  # type: ignore[arg-type]
            severity="low",
            title="x",
            body="y",
            highlight={"value": "1"},
        )


def test_share_request_response() -> None:
    report = _minimal_report()
    req = ShareCreateRequest(report=report)
    assert req.report.dials.recovery.value == 70.0

    resp = ShareCreateResponse(
        id="abc12345",
        url="/r/abc12345",
        expires_at=datetime(2026, 5, 7, tzinfo=timezone.utc),
    )
    data = resp.model_dump(mode="json")
    assert data["url"] == "/r/abc12345"
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/test_models.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.models'`.

- [ ] **Step 3: Implement `models/__init__.py`**

Create `apps/api/app/models/__init__.py`:

```python
"""Pydantic models — the public API contract.

These match `apps/web/src/lib/types.ts` 1:1. When you change one, change both.
"""
```

- [ ] **Step 4: Implement `models/insight.py`**

Create `apps/api/app/models/insight.py`:

```python
from typing import Literal

from pydantic import BaseModel

InsightKind = Literal[
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
]

InsightSeverity = Literal["low", "medium", "high"]


class InsightHighlight(BaseModel):
    value: str
    unit: str | None = None


class InsightEvidence(BaseModel):
    value: float
    label: str


class Insight(BaseModel):
    kind: InsightKind
    severity: InsightSeverity
    title: str
    body: str
    highlight: InsightHighlight
    evidence: list[InsightEvidence] | None = None
```

- [ ] **Step 5: Implement `models/report.py`**

Create `apps/api/app/models/report.py`:

```python
from typing import Literal

from pydantic import BaseModel, Field

from app.models.insight import Insight


class Period(BaseModel):
    start: str  # ISO 8601 date
    end: str
    days: int


class DialMetric(BaseModel):
    value: float
    unit: Literal["h", "%", ""]
    # exactly one of these is set per dial; we keep both as Optional for typing
    performance_pct: float | None = None  # sleep
    green_pct: float | None = None  # recovery
    label: Literal["light", "moderate", "high", "all_out"] | None = None  # strain


class Dials(BaseModel):
    sleep: DialMetric
    recovery: DialMetric
    strain: DialMetric


class Metrics(BaseModel):
    hrv_ms: float
    rhr_bpm: float
    resp_rpm: float
    spo2_pct: float
    sleep_efficiency_pct: float
    sleep_consistency_pct: float
    sleep_debt_min: float


class TrendPoint(BaseModel):
    date: str  # ISO date
    value: float | None


DowName = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class DowEntry(BaseModel):
    dow: DowName
    mean: float
    n: int


class SickEpisode(BaseModel):
    date: str
    recovery: float
    rhr: float
    hrv: float
    skin_temp_c: float | None


class RecoveryDistribution(BaseModel):
    green: float
    yellow: float
    red: float


class RecoverySection(BaseModel):
    trend: list[TrendPoint]
    by_dow: list[DowEntry]
    distribution: RecoveryDistribution
    sick_episodes: list[SickEpisode]


class HypnogramSegment(BaseModel):
    stage: Literal["awake", "light", "rem", "deep"]
    from_: str = Field(..., alias="from")
    to: str

    model_config = {"populate_by_name": True}


class HypnogramNight(BaseModel):
    start: str
    end: str
    segments: list[HypnogramSegment]


class BedtimeStrip(BaseModel):
    date: str
    bed_local: str  # "HH:MM"
    wake_local: str


class SleepDurations(BaseModel):
    light_min: float
    rem_min: float
    deep_min: float
    awake_min: float


class SleepStagePct(BaseModel):
    light: float
    rem: float
    deep: float


class SleepSection(BaseModel):
    avg_bedtime: str  # "HH:MM"
    avg_wake: str
    bedtime_std_h: float
    avg_durations: SleepDurations
    stage_pct: SleepStagePct
    hypnogram_sample: HypnogramNight | None
    consistency_strip: list[BedtimeStrip]


class StrainDistribution(BaseModel):
    light: float
    moderate: float
    high: float
    all_out: float


class StrainSection(BaseModel):
    avg_strain: float
    distribution: StrainDistribution
    trend: list[TrendPoint]


class ActivityAgg(BaseModel):
    name: str
    count: int
    total_strain: float
    total_min: float
    pct_of_total_strain: float


class TopStrainDay(BaseModel):
    date: str
    day_strain: float
    recovery: float
    next_recovery: float | None


class WorkoutsSection(BaseModel):
    total: int
    by_activity: list[ActivityAgg]
    top_strain_days: list[TopStrainDay]


class JournalQuestionAgg(BaseModel):
    question: str
    yes: int
    no: int
    mean_rec_yes: float | None
    mean_rec_no: float | None


class JournalSection(BaseModel):
    days_logged: int
    questions: list[JournalQuestionAgg]
    note: str


class MonthlyAgg(BaseModel):
    month: str  # "YYYY-MM"
    recovery: float
    hrv: float
    rhr: float
    sleep_h: float


class TrendComparison(BaseModel):
    # tuples are (first_60d_value, last_60d_value)
    bedtime_h: tuple[float, float]
    sleep_h: tuple[float, float]
    rhr: tuple[float, float]
    workouts: tuple[int, int]


class TrendsSection(BaseModel):
    monthly: list[MonthlyAgg]
    first_vs_last_60d: TrendComparison


class WhoopReport(BaseModel):
    schema_version: Literal[1] = 1
    period: Period
    dials: Dials
    metrics: Metrics
    recovery: RecoverySection
    sleep: SleepSection
    strain: StrainSection
    workouts: WorkoutsSection | None
    journal: JournalSection | None
    trends: TrendsSection
    insights: list[Insight]
```

- [ ] **Step 6: Implement `models/share.py`**

Create `apps/api/app/models/share.py`:

```python
from datetime import datetime

from pydantic import BaseModel

from app.models.report import WhoopReport


class ShareCreateRequest(BaseModel):
    report: WhoopReport


class ShareCreateResponse(BaseModel):
    id: str
    url: str
    expires_at: datetime
```

- [ ] **Step 7: Run the model tests**

```bash
uv run pytest tests/test_models.py -v
```

Expected: `3 passed`.

- [ ] **Step 8: Commit**

```bash
git add apps/api/
git commit -m "feat(api): add Pydantic models for WhoopReport contract

- Insight, InsightKind, InsightSeverity literals
- Full WhoopReport tree with nested sections matching the spec
- ShareCreateRequest/Response
- Round-trip + literal-validation tests passing"
```

---

## Task 4: CSV schemas and parser errors

**Files:**
- Create: `apps/api/app/parsing/__init__.py`
- Create: `apps/api/app/parsing/errors.py`
- Create: `apps/api/app/parsing/csv_schema.py`
- Create: `apps/api/tests/parsing/__init__.py`
- Create: `apps/api/tests/parsing/test_csv_schema.py`

- [ ] **Step 1: Write the schema test**

Create `apps/api/tests/parsing/__init__.py` (empty), then `apps/api/tests/parsing/test_csv_schema.py`:

```python
import pytest

from app.parsing.csv_schema import (
    CYCLES_REQUIRED_COLUMNS,
    JOURNAL_REQUIRED_COLUMNS,
    SLEEPS_REQUIRED_COLUMNS,
    WORKOUTS_REQUIRED_COLUMNS,
    CsvFile,
    validate_columns,
)
from app.parsing.errors import UnexpectedSchemaError


def test_cycles_columns_listed() -> None:
    assert "Recovery score %" in CYCLES_REQUIRED_COLUMNS
    assert "Heart rate variability (ms)" in CYCLES_REQUIRED_COLUMNS
    assert "Sleep onset" in CYCLES_REQUIRED_COLUMNS


def test_validate_columns_happy() -> None:
    extra = ["A useless extra column"]
    validate_columns(
        CsvFile.CYCLES,
        list(CYCLES_REQUIRED_COLUMNS) + extra,
    )


def test_validate_columns_missing_required() -> None:
    cols = [c for c in CYCLES_REQUIRED_COLUMNS if c != "Recovery score %"]
    with pytest.raises(UnexpectedSchemaError) as exc:
        validate_columns(CsvFile.CYCLES, cols)
    assert "Recovery score %" in exc.value.missing
    assert exc.value.file == "physiological_cycles.csv"


def test_validate_columns_for_each_file() -> None:
    validate_columns(CsvFile.CYCLES, list(CYCLES_REQUIRED_COLUMNS))
    validate_columns(CsvFile.SLEEPS, list(SLEEPS_REQUIRED_COLUMNS))
    validate_columns(CsvFile.WORKOUTS, list(WORKOUTS_REQUIRED_COLUMNS))
    validate_columns(CsvFile.JOURNAL, list(JOURNAL_REQUIRED_COLUMNS))
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/parsing/test_csv_schema.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.parsing'`.

- [ ] **Step 3: Implement `parsing/__init__.py`**

Create `apps/api/app/parsing/__init__.py` (empty file).

- [ ] **Step 4: Implement `parsing/errors.py`**

Create `apps/api/app/parsing/errors.py`:

```python
class ParseError(Exception):
    """Base class for all parsing errors that should become 400 responses."""

    code: str = "parse_error"


class NotAZipError(ParseError):
    code = "not_a_zip"


class CorruptZipError(ParseError):
    code = "corrupt_zip"


class FileTooLargeError(ParseError):
    code = "file_too_large"

    def __init__(self, limit_mb: int) -> None:
        super().__init__(f"file larger than {limit_mb} MB")
        self.limit_mb = limit_mb


class MissingRequiredFileError(ParseError):
    code = "missing_required_file"

    def __init__(self, filename: str) -> None:
        super().__init__(f"missing required file: {filename}")
        self.file = filename


class UnexpectedSchemaError(ParseError):
    code = "unexpected_schema"

    def __init__(
        self,
        file: str,
        missing: list[str],
        extra: list[str],
    ) -> None:
        super().__init__(f"{file} has unexpected schema")
        self.file = file
        self.missing = missing
        self.extra = extra


class NoDataError(ParseError):
    code = "no_data"

    def __init__(self, filename: str) -> None:
        super().__init__(f"{filename} contains no data rows")
        self.file = filename
```

- [ ] **Step 5: Implement `parsing/csv_schema.py`**

Create `apps/api/app/parsing/csv_schema.py`:

```python
"""Source of truth for the column shapes we expect in the Whoop export.

Column lists are taken from a real Whoop export (April 2026 format). If Whoop
changes the export, only this file should need to update.
"""
from enum import Enum

from app.parsing.errors import UnexpectedSchemaError


class CsvFile(str, Enum):
    CYCLES = "physiological_cycles.csv"
    SLEEPS = "sleeps.csv"
    WORKOUTS = "workouts.csv"
    JOURNAL = "journal_entries.csv"


CYCLES_REQUIRED_COLUMNS: tuple[str, ...] = (
    "Cycle start time",
    "Cycle end time",
    "Cycle timezone",
    "Recovery score %",
    "Resting heart rate (bpm)",
    "Heart rate variability (ms)",
    "Skin temp (celsius)",
    "Blood oxygen %",
    "Day Strain",
    "Energy burned (cal)",
    "Max HR (bpm)",
    "Average HR (bpm)",
    "Sleep onset",
    "Wake onset",
    "Sleep performance %",
    "Respiratory rate (rpm)",
    "Asleep duration (min)",
    "In bed duration (min)",
    "Light sleep duration (min)",
    "Deep (SWS) duration (min)",
    "REM duration (min)",
    "Awake duration (min)",
    "Sleep need (min)",
    "Sleep debt (min)",
    "Sleep efficiency %",
    "Sleep consistency %",
)

SLEEPS_REQUIRED_COLUMNS: tuple[str, ...] = (
    "Cycle start time",
    "Cycle end time",
    "Cycle timezone",
    "Sleep onset",
    "Wake onset",
    "Sleep performance %",
    "Respiratory rate (rpm)",
    "Asleep duration (min)",
    "In bed duration (min)",
    "Light sleep duration (min)",
    "Deep (SWS) duration (min)",
    "REM duration (min)",
    "Awake duration (min)",
    "Sleep need (min)",
    "Sleep debt (min)",
    "Sleep efficiency %",
    "Sleep consistency %",
    "Nap",
)

WORKOUTS_REQUIRED_COLUMNS: tuple[str, ...] = (
    "Cycle start time",
    "Cycle end time",
    "Cycle timezone",
    "Workout start time",
    "Workout end time",
    "Duration (min)",
    "Activity name",
    "Activity Strain",
    "Energy burned (cal)",
    "Max HR (bpm)",
    "Average HR (bpm)",
    "HR Zone 1 %",
    "HR Zone 2 %",
    "HR Zone 3 %",
    "HR Zone 4 %",
    "HR Zone 5 %",
    "GPS enabled",
)

JOURNAL_REQUIRED_COLUMNS: tuple[str, ...] = (
    "Cycle start time",
    "Cycle end time",
    "Cycle timezone",
    "Question text",
    "Answered yes",
    "Notes",
)


_REQUIRED: dict[CsvFile, tuple[str, ...]] = {
    CsvFile.CYCLES: CYCLES_REQUIRED_COLUMNS,
    CsvFile.SLEEPS: SLEEPS_REQUIRED_COLUMNS,
    CsvFile.WORKOUTS: WORKOUTS_REQUIRED_COLUMNS,
    CsvFile.JOURNAL: JOURNAL_REQUIRED_COLUMNS,
}


def validate_columns(file: CsvFile, actual: list[str]) -> None:
    required = set(_REQUIRED[file])
    actual_set = set(actual)
    missing = sorted(required - actual_set)
    if missing:
        extra = sorted(actual_set - required)
        raise UnexpectedSchemaError(file=file.value, missing=missing, extra=extra)
```

- [ ] **Step 6: Run the schema tests**

```bash
uv run pytest tests/parsing/test_csv_schema.py -v
```

Expected: `4 passed`.

- [ ] **Step 7: Commit**

```bash
git add apps/api/
git commit -m "feat(api): add CSV column schemas and parsing error hierarchy

- ParseError base + 6 typed subclasses (each with a stable .code)
- Required column lists for the 4 Whoop CSVs (April 2026 format)
- validate_columns() raises UnexpectedSchemaError with missing/extra
- Schema tests cover happy + missing-required + each file type"
```

---

## Task 5: Build deterministic fixture zips

**Files:**
- Create: `apps/api/tests/fixtures/__init__.py`
- Create: `apps/api/tests/fixtures/build_fixtures.py`
- Create: `apps/api/tests/fixtures/zips/.gitkeep`
- Create: `apps/api/tests/fixtures/test_build_fixtures.py`

- [ ] **Step 1: Plan the fixture shapes**

We need synthetic but realistic fixtures. The "happy" fixture is a 60-day export with statistically stable inputs so the snapshot is deterministic. We use a fixed RNG seed.

- [ ] **Step 2: Write the fixtures-build test**

Create `apps/api/tests/fixtures/__init__.py` (empty), then `apps/api/tests/fixtures/test_build_fixtures.py`:

```python
import zipfile
from pathlib import Path

import pytest

from tests.fixtures.build_fixtures import (
    HAPPY_DAYS,
    build_all_fixtures,
    fixtures_dir,
)


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures_built() -> None:
    build_all_fixtures()


def test_happy_zip_exists_and_has_4_files() -> None:
    p = fixtures_dir() / "happy.zip"
    assert p.exists()
    with zipfile.ZipFile(p) as zf:
        names = sorted(zf.namelist())
    assert names == sorted(
        [
            "physiological_cycles.csv",
            "sleeps.csv",
            "workouts.csv",
            "journal_entries.csv",
        ]
    )


def test_happy_cycles_has_correct_row_count() -> None:
    import csv
    p = fixtures_dir() / "happy.zip"
    with zipfile.ZipFile(p) as zf, zf.open("physiological_cycles.csv") as f:
        reader = csv.reader(line.decode("utf-8") for line in f.readlines())
        rows = list(reader)
    # header + HAPPY_DAYS rows
    assert len(rows) == HAPPY_DAYS + 1


def test_minimal_zip_has_14_days() -> None:
    import csv
    p = fixtures_dir() / "minimal_14d.zip"
    with zipfile.ZipFile(p) as zf, zf.open("physiological_cycles.csv") as f:
        rows = list(csv.reader(line.decode("utf-8") for line in f.readlines()))
    assert len(rows) == 15  # 14 + header


def test_no_workouts_zip_has_empty_workouts() -> None:
    import csv
    p = fixtures_dir() / "no_workouts.zip"
    with zipfile.ZipFile(p) as zf, zf.open("workouts.csv") as f:
        rows = list(csv.reader(line.decode("utf-8") for line in f.readlines()))
    assert len(rows) == 1  # only header


def test_corrupt_zip_is_invalid() -> None:
    p = fixtures_dir() / "corrupt.zip"
    with pytest.raises(zipfile.BadZipFile):
        zipfile.ZipFile(p)


def test_wrong_format_zip_has_renamed_column() -> None:
    p = fixtures_dir() / "wrong_format.zip"
    with zipfile.ZipFile(p) as zf, zf.open("physiological_cycles.csv") as f:
        header = f.readline().decode("utf-8").strip()
    assert "Recovery score %" not in header
```

- [ ] **Step 3: Run to confirm failure**

```bash
uv run pytest tests/fixtures/test_build_fixtures.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 4: Implement the fixture builder**

Create `apps/api/tests/fixtures/zips/.gitkeep` (empty file).

Create `apps/api/tests/fixtures/build_fixtures.py`:

```python
"""Generate deterministic fixture zips for the parser and pipeline tests.

Uses a seeded numpy RNG so the snapshot tests are stable across machines.
"""
import csv
import io
import random
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

from app.parsing.csv_schema import (
    CYCLES_REQUIRED_COLUMNS,
    JOURNAL_REQUIRED_COLUMNS,
    SLEEPS_REQUIRED_COLUMNS,
    WORKOUTS_REQUIRED_COLUMNS,
)

HAPPY_DAYS = 60
MINIMAL_DAYS = 14
SEED = 42
START_DATE = datetime(2025, 1, 1, 23, 30, 0)


def fixtures_dir() -> Path:
    return Path(__file__).parent / "zips"


def _cycles_row(day: int, rng: random.Random) -> dict[str, str]:
    start = START_DATE + timedelta(days=day)
    end = start + timedelta(hours=10)
    sleep_min = 420 + rng.randint(0, 120)
    deep = 90 + rng.randint(0, 30)
    rem = 90 + rng.randint(0, 40)
    awake = 30 + rng.randint(0, 30)
    light = sleep_min - deep - rem
    return {
        "Cycle start time": start.strftime("%Y-%m-%d %H:%M:%S"),
        "Cycle end time": end.strftime("%Y-%m-%d %H:%M:%S"),
        "Cycle timezone": "UTC+05:00",
        "Recovery score %": str(60 + rng.randint(0, 30)),
        "Resting heart rate (bpm)": str(48 + rng.randint(0, 6)),
        "Heart rate variability (ms)": str(110 + rng.randint(0, 30)),
        "Skin temp (celsius)": f"{33.5 + rng.random():.2f}",
        "Blood oxygen %": f"{94 + rng.random() * 2:.2f}",
        "Day Strain": f"{8 + rng.random() * 6:.1f}",
        "Energy burned (cal)": str(1700 + rng.randint(0, 600)),
        "Max HR (bpm)": str(150 + rng.randint(0, 30)),
        "Average HR (bpm)": str(70 + rng.randint(0, 20)),
        "Sleep onset": start.strftime("%Y-%m-%d %H:%M:%S"),
        "Wake onset": (start + timedelta(minutes=sleep_min + awake)).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "Sleep performance %": str(75 + rng.randint(0, 20)),
        "Respiratory rate (rpm)": f"{14.5 + rng.random():.2f}",
        "Asleep duration (min)": str(sleep_min),
        "In bed duration (min)": str(sleep_min + awake),
        "Light sleep duration (min)": str(light),
        "Deep (SWS) duration (min)": str(deep),
        "REM duration (min)": str(rem),
        "Awake duration (min)": str(awake),
        "Sleep need (min)": "480",
        "Sleep debt (min)": "0",
        "Sleep efficiency %": "92",
        "Sleep consistency %": "65",
    }


def _sleeps_row_from_cycle(c: dict[str, str]) -> dict[str, str]:
    return {col: c.get(col, "") for col in SLEEPS_REQUIRED_COLUMNS} | {"Nap": "false"}


def _workout_row(day: int, rng: random.Random) -> dict[str, str]:
    start = START_DATE + timedelta(days=day, hours=14)
    end = start + timedelta(minutes=30)
    return {
        "Cycle start time": (START_DATE + timedelta(days=day)).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "Cycle end time": (START_DATE + timedelta(days=day + 1)).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "Cycle timezone": "UTC+05:00",
        "Workout start time": start.strftime("%Y-%m-%d %H:%M:%S"),
        "Workout end time": end.strftime("%Y-%m-%d %H:%M:%S"),
        "Duration (min)": "30",
        "Activity name": "Walking",
        "Activity Strain": f"{6 + rng.random() * 3:.1f}",
        "Energy burned (cal)": str(200 + rng.randint(0, 100)),
        "Max HR (bpm)": str(140 + rng.randint(0, 20)),
        "Average HR (bpm)": str(110 + rng.randint(0, 15)),
        "HR Zone 1 %": "60",
        "HR Zone 2 %": "30",
        "HR Zone 3 %": "10",
        "HR Zone 4 %": "0",
        "HR Zone 5 %": "0",
        "GPS enabled": "false",
    }


def _journal_row(day: int) -> dict[str, str]:
    cs = (START_DATE + timedelta(days=day)).strftime("%Y-%m-%d %H:%M:%S")
    return {
        "Cycle start time": cs,
        "Cycle end time": (START_DATE + timedelta(days=day + 1)).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "Cycle timezone": "UTC+05:00",
        "Question text": "Hydrated sufficiently?",
        "Answered yes": "true",
        "Notes": "",
    }


def _csv_bytes(rows: list[dict[str, str]], columns: tuple[str, ...]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(columns))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def _empty_csv_bytes(columns: tuple[str, ...]) -> bytes:
    return _csv_bytes([], columns)


def _build_zip(
    target: Path,
    days: int,
    *,
    include_workouts: bool = True,
    include_journal: bool = True,
) -> None:
    rng = random.Random(SEED)
    cycles = [_cycles_row(d, rng) for d in range(days)]
    sleeps = [_sleeps_row_from_cycle(c) for c in cycles]
    workouts = [_workout_row(d, rng) for d in range(days // 3)] if include_workouts else []
    journal = [_journal_row(d) for d in range(days // 2)] if include_journal else []

    cycles_bytes = _csv_bytes(cycles, CYCLES_REQUIRED_COLUMNS)
    sleeps_bytes = _csv_bytes(sleeps, SLEEPS_REQUIRED_COLUMNS)
    workouts_bytes = (
        _csv_bytes(workouts, WORKOUTS_REQUIRED_COLUMNS)
        if include_workouts
        else _empty_csv_bytes(WORKOUTS_REQUIRED_COLUMNS)
    )
    journal_bytes = (
        _csv_bytes(journal, JOURNAL_REQUIRED_COLUMNS)
        if include_journal
        else _empty_csv_bytes(JOURNAL_REQUIRED_COLUMNS)
    )

    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("physiological_cycles.csv", cycles_bytes)
        zf.writestr("sleeps.csv", sleeps_bytes)
        zf.writestr("workouts.csv", workouts_bytes)
        zf.writestr("journal_entries.csv", journal_bytes)


def build_corrupt_zip(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"this is not a zip file at all\x00\x01\x02")


def build_wrong_format_zip(target: Path) -> None:
    rng = random.Random(SEED)
    rows = [_cycles_row(d, rng) for d in range(5)]
    # Replace one required column name with garbage
    bad_columns = tuple(
        "Recovery_score" if c == "Recovery score %" else c
        for c in CYCLES_REQUIRED_COLUMNS
    )
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(bad_columns))
    writer.writeheader()
    for row in rows:
        renamed = {
            ("Recovery_score" if k == "Recovery score %" else k): v for k, v in row.items()
        }
        writer.writerow(renamed)
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("physiological_cycles.csv", buf.getvalue())
        zf.writestr("sleeps.csv", _empty_csv_bytes(SLEEPS_REQUIRED_COLUMNS))
        zf.writestr("workouts.csv", _empty_csv_bytes(WORKOUTS_REQUIRED_COLUMNS))
        zf.writestr("journal_entries.csv", _empty_csv_bytes(JOURNAL_REQUIRED_COLUMNS))


def build_all_fixtures() -> None:
    d = fixtures_dir()
    _build_zip(d / "happy.zip", HAPPY_DAYS, include_workouts=True, include_journal=True)
    _build_zip(d / "minimal_14d.zip", MINIMAL_DAYS)
    _build_zip(d / "no_workouts.zip", HAPPY_DAYS, include_workouts=False)
    _build_zip(d / "no_journal.zip", HAPPY_DAYS, include_journal=False)
    build_corrupt_zip(d / "corrupt.zip")
    build_wrong_format_zip(d / "wrong_format.zip")


if __name__ == "__main__":
    build_all_fixtures()
    print(f"fixtures built in {fixtures_dir()}")
```

- [ ] **Step 5: Make `tests/__init__.py` and `tests/fixtures/__init__.py` real packages**

Confirm both `__init__.py` files exist (the test imports `tests.fixtures.build_fixtures`):

```bash
ls apps/api/tests/__init__.py apps/api/tests/fixtures/__init__.py
```

Both should exist as empty files (Task 1 created the first, Step 2 above created the second).

- [ ] **Step 6: Build the fixtures and run tests**

```bash
uv run python -m tests.fixtures.build_fixtures
uv run pytest tests/fixtures/test_build_fixtures.py -v
```

Expected: First command prints `fixtures built in ...`. All tests pass.

- [ ] **Step 7: Commit (with the .zip artifacts)**

```bash
git add apps/api/tests/
git commit -m "test(api): add deterministic fixture zip builder

- Builds 6 fixture zips: happy, minimal_14d, no_workouts, no_journal,
  corrupt, wrong_format
- Seeded RNG so snapshot tests are stable
- Tests verify zip contents and edge-case shape"
```

---

## Task 6: ZIP loader (open + locate + size limit)

**Files:**
- Create: `apps/api/app/parsing/zip_loader.py`
- Create: `apps/api/tests/parsing/test_zip_loader.py`

- [ ] **Step 1: Write the loader test**

Create `apps/api/tests/parsing/test_zip_loader.py`:

```python
from pathlib import Path

import pytest

from app.parsing.csv_schema import CsvFile
from app.parsing.errors import (
    CorruptZipError,
    FileTooLargeError,
    MissingRequiredFileError,
    NotAZipError,
)
from app.parsing.zip_loader import LoadedZip, load_zip
from tests.fixtures.build_fixtures import build_all_fixtures, fixtures_dir


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures() -> None:
    build_all_fixtures()


def test_loads_happy_zip() -> None:
    z: LoadedZip = load_zip(fixtures_dir() / "happy.zip", max_bytes=50 * 1024 * 1024)
    assert set(z.files.keys()) == {f for f in CsvFile}
    assert z.files[CsvFile.CYCLES].startswith(b"Cycle start time")


def test_loads_no_workouts_zip() -> None:
    z = load_zip(fixtures_dir() / "no_workouts.zip", max_bytes=50 * 1024 * 1024)
    assert CsvFile.WORKOUTS in z.files
    # workouts is empty (header only)
    workouts_text = z.files[CsvFile.WORKOUTS].decode()
    assert workouts_text.strip().count("\n") == 0


def test_corrupt_zip_raises() -> None:
    with pytest.raises(CorruptZipError):
        load_zip(fixtures_dir() / "corrupt.zip", max_bytes=50 * 1024 * 1024)


def test_not_a_zip_raises(tmp_path: Path) -> None:
    p = tmp_path / "thing.txt"
    p.write_bytes(b"hello")
    with pytest.raises(NotAZipError):
        load_zip(p, max_bytes=50 * 1024 * 1024)


def test_oversized_zip_raises(tmp_path: Path) -> None:
    p = tmp_path / "big.zip"
    p.write_bytes(b"PK\x03\x04" + b"\x00" * 1024)  # zip-ish prefix
    with pytest.raises((FileTooLargeError, NotAZipError, CorruptZipError)):
        load_zip(p, max_bytes=10)


def test_missing_required_file(tmp_path: Path) -> None:
    import zipfile
    p = tmp_path / "incomplete.zip"
    with zipfile.ZipFile(p, "w") as zf:
        zf.writestr("sleeps.csv", "Cycle start time\n")
    with pytest.raises(MissingRequiredFileError) as exc:
        load_zip(p, max_bytes=50 * 1024 * 1024)
    assert exc.value.file == "physiological_cycles.csv"
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/parsing/test_zip_loader.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.parsing.zip_loader'`.

- [ ] **Step 3: Implement `zip_loader.py`**

Create `apps/api/app/parsing/zip_loader.py`:

```python
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from app.parsing.csv_schema import CsvFile
from app.parsing.errors import (
    CorruptZipError,
    FileTooLargeError,
    MissingRequiredFileError,
    NotAZipError,
)

REQUIRED_FILES: frozenset[CsvFile] = frozenset({CsvFile.CYCLES, CsvFile.SLEEPS})
OPTIONAL_FILES: frozenset[CsvFile] = frozenset({CsvFile.WORKOUTS, CsvFile.JOURNAL})

MAX_EXTRACTED_BYTES = 200 * 1024 * 1024  # 200 MB total uncompressed cap


@dataclass(frozen=True)
class LoadedZip:
    files: dict[CsvFile, bytes]


def load_zip(source: Path | BinaryIO, *, max_bytes: int) -> LoadedZip:
    """Load a Whoop export ZIP and return its CSV files as bytes.

    Raises ParseError subclasses for any failure mode.
    """
    if isinstance(source, Path):
        size = source.stat().st_size
        if size > max_bytes:
            raise FileTooLargeError(limit_mb=max_bytes // (1024 * 1024))
        opener: object = source
    else:
        opener = source

    try:
        zf = zipfile.ZipFile(opener)
    except zipfile.BadZipFile as e:
        # distinguish "not a zip" from "corrupt zip"
        if isinstance(opener, Path):
            head = opener.read_bytes()[:4]
        else:
            opener.seek(0)
            head = opener.read(4)
            opener.seek(0)
        if not head.startswith(b"PK"):
            raise NotAZipError(str(e)) from e
        raise CorruptZipError(str(e)) from e

    try:
        names = {name.lower(): name for name in zf.namelist()}
        files: dict[CsvFile, bytes] = {}
        total_bytes = 0
        for csv_file in CsvFile:
            actual_name = names.get(csv_file.value.lower())
            if actual_name is None:
                if csv_file in REQUIRED_FILES:
                    raise MissingRequiredFileError(csv_file.value)
                continue
            with zf.open(actual_name) as f:
                content = f.read(MAX_EXTRACTED_BYTES + 1)
            if len(content) > MAX_EXTRACTED_BYTES:
                raise CorruptZipError("uncompressed payload exceeds 200 MB")
            total_bytes += len(content)
            if total_bytes > MAX_EXTRACTED_BYTES:
                raise CorruptZipError("uncompressed payload exceeds 200 MB")
            files[csv_file] = content

        # Always include the optional files (empty if missing) so consumers
        # don't have to KeyError-check.
        for csv_file in OPTIONAL_FILES:
            files.setdefault(csv_file, b"")

        return LoadedZip(files=files)
    finally:
        zf.close()
```

- [ ] **Step 4: Run the loader tests**

```bash
uv run pytest tests/parsing/test_zip_loader.py -v
```

Expected: `6 passed`.

- [ ] **Step 5: Commit**

```bash
git add apps/api/
git commit -m "feat(api): add zip_loader with size + corruption + missing-file checks

- LoadedZip dataclass holds bytes per CsvFile
- Distinguishes not-a-zip vs corrupt-zip vs missing-required-file
- 200 MB uncompressed cap (zip-bomb protection)
- Optional files always present in result (empty bytes if missing)
- 6 loader tests passing"
```

---

## Task 7: Frame parsing (CSV bytes → typed pandas DataFrames)

**Files:**
- Create: `apps/api/app/parsing/frames.py`
- Create: `apps/api/tests/parsing/test_frames.py`
- Modify: `apps/api/pyproject.toml` (add pandas, numpy)

- [ ] **Step 1: Add pandas + numpy to dependencies**

```bash
cd ~/projects/whoop-lens/apps/api
uv add "pandas>=2.2" "numpy>=2.0"
```

- [ ] **Step 2: Write the frames test**

Create `apps/api/tests/parsing/test_frames.py`:

```python
import pytest

from app.parsing.errors import NoDataError, UnexpectedSchemaError
from app.parsing.frames import ParsedFrames, parse_frames
from app.parsing.zip_loader import load_zip
from tests.fixtures.build_fixtures import build_all_fixtures, fixtures_dir


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures() -> None:
    build_all_fixtures()


def test_parse_happy_frames() -> None:
    z = load_zip(fixtures_dir() / "happy.zip", max_bytes=50 * 1024 * 1024)
    f: ParsedFrames = parse_frames(z)
    assert len(f.cycles) == 60
    assert len(f.sleeps) == 60
    assert len(f.workouts) > 0
    assert len(f.journal) > 0
    assert f.cycles["Recovery score %"].dtype.kind == "f"
    assert "Cycle start time" in f.cycles.columns


def test_parse_no_workouts_frames() -> None:
    z = load_zip(fixtures_dir() / "no_workouts.zip", max_bytes=50 * 1024 * 1024)
    f = parse_frames(z)
    assert len(f.cycles) == 60
    assert len(f.workouts) == 0


def test_parse_no_journal_frames() -> None:
    z = load_zip(fixtures_dir() / "no_journal.zip", max_bytes=50 * 1024 * 1024)
    f = parse_frames(z)
    assert len(f.cycles) == 60
    assert len(f.journal) == 0


def test_parse_wrong_format_raises() -> None:
    z = load_zip(fixtures_dir() / "wrong_format.zip", max_bytes=50 * 1024 * 1024)
    with pytest.raises(UnexpectedSchemaError):
        parse_frames(z)


def test_parse_empty_cycles_raises(tmp_path: object) -> None:
    import zipfile
    from app.parsing.csv_schema import (
        CYCLES_REQUIRED_COLUMNS,
        SLEEPS_REQUIRED_COLUMNS,
        JOURNAL_REQUIRED_COLUMNS,
        WORKOUTS_REQUIRED_COLUMNS,
    )
    p = tmp_path / "empty.zip"  # type: ignore[operator]
    with zipfile.ZipFile(p, "w") as zf:
        zf.writestr(
            "physiological_cycles.csv", ",".join(CYCLES_REQUIRED_COLUMNS) + "\n"
        )
        zf.writestr("sleeps.csv", ",".join(SLEEPS_REQUIRED_COLUMNS) + "\n")
        zf.writestr("workouts.csv", ",".join(WORKOUTS_REQUIRED_COLUMNS) + "\n")
        zf.writestr("journal_entries.csv", ",".join(JOURNAL_REQUIRED_COLUMNS) + "\n")
    z = load_zip(p, max_bytes=50 * 1024 * 1024)
    with pytest.raises(NoDataError) as exc:
        parse_frames(z)
    assert exc.value.file == "physiological_cycles.csv"
```

- [ ] **Step 3: Run to confirm failure**

```bash
uv run pytest tests/parsing/test_frames.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.parsing.frames'`.

- [ ] **Step 4: Implement `frames.py`**

Create `apps/api/app/parsing/frames.py`:

```python
"""Parse loaded CSV bytes into typed pandas DataFrames.

We always read as strings first, validate columns, then explicitly coerce
each column with the right dtype. Rows with NaT timestamps are dropped;
rows with all-NaN are dropped; everything else is left for the analysis
layer to handle.
"""
import io
from dataclasses import dataclass

import pandas as pd

from app.parsing.csv_schema import (
    CYCLES_REQUIRED_COLUMNS,
    JOURNAL_REQUIRED_COLUMNS,
    SLEEPS_REQUIRED_COLUMNS,
    WORKOUTS_REQUIRED_COLUMNS,
    CsvFile,
    validate_columns,
)
from app.parsing.errors import NoDataError
from app.parsing.zip_loader import LoadedZip

# Columns that should be parsed as datetimes (where present)
DATETIME_COLUMNS: set[str] = {
    "Cycle start time",
    "Cycle end time",
    "Sleep onset",
    "Wake onset",
    "Workout start time",
    "Workout end time",
}

# Columns that should be parsed as floats (where present)
FLOAT_COLUMNS: set[str] = {
    "Recovery score %",
    "Resting heart rate (bpm)",
    "Heart rate variability (ms)",
    "Skin temp (celsius)",
    "Blood oxygen %",
    "Day Strain",
    "Energy burned (cal)",
    "Max HR (bpm)",
    "Average HR (bpm)",
    "Sleep performance %",
    "Respiratory rate (rpm)",
    "Asleep duration (min)",
    "In bed duration (min)",
    "Light sleep duration (min)",
    "Deep (SWS) duration (min)",
    "REM duration (min)",
    "Awake duration (min)",
    "Sleep need (min)",
    "Sleep debt (min)",
    "Sleep efficiency %",
    "Sleep consistency %",
    "Duration (min)",
    "Activity Strain",
    "HR Zone 1 %",
    "HR Zone 2 %",
    "HR Zone 3 %",
    "HR Zone 4 %",
    "HR Zone 5 %",
}


@dataclass(frozen=True)
class ParsedFrames:
    cycles: pd.DataFrame
    sleeps: pd.DataFrame
    workouts: pd.DataFrame
    journal: pd.DataFrame


def _read_csv_strict(content: bytes, file: CsvFile) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False, na_values=[""])
    validate_columns(file, df.columns.tolist())
    return df


def _coerce_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if col in DATETIME_COLUMNS:
            df[col] = pd.to_datetime(df[col], errors="coerce")
        elif col in FLOAT_COLUMNS:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def parse_frames(loaded: LoadedZip) -> ParsedFrames:
    cycles_raw = _read_csv_strict(loaded.files[CsvFile.CYCLES], CsvFile.CYCLES)
    sleeps_raw = _read_csv_strict(loaded.files[CsvFile.SLEEPS], CsvFile.SLEEPS)

    cycles = _coerce_columns(cycles_raw)
    cycles = cycles.dropna(subset=["Cycle start time"])
    if cycles.empty:
        raise NoDataError(CsvFile.CYCLES.value)

    sleeps = _coerce_columns(sleeps_raw)
    sleeps = sleeps.dropna(subset=["Cycle start time"])

    workouts_bytes = loaded.files.get(CsvFile.WORKOUTS, b"")
    if workouts_bytes:
        workouts_raw = _read_csv_strict(workouts_bytes, CsvFile.WORKOUTS)
        workouts = _coerce_columns(workouts_raw)
        workouts = workouts.dropna(subset=["Workout start time"])
    else:
        workouts = pd.DataFrame(columns=list(WORKOUTS_REQUIRED_COLUMNS))

    journal_bytes = loaded.files.get(CsvFile.JOURNAL, b"")
    if journal_bytes:
        journal_raw = _read_csv_strict(journal_bytes, CsvFile.JOURNAL)
        journal = _coerce_columns(journal_raw)
    else:
        journal = pd.DataFrame(columns=list(JOURNAL_REQUIRED_COLUMNS))

    return ParsedFrames(
        cycles=cycles.reset_index(drop=True),
        sleeps=sleeps.reset_index(drop=True),
        workouts=workouts.reset_index(drop=True),
        journal=journal.reset_index(drop=True),
    )
```

- [ ] **Step 5: Run frames tests**

```bash
uv run pytest tests/parsing/test_frames.py -v
```

Expected: `5 passed`.

- [ ] **Step 6: Commit**

```bash
git add apps/api/
git commit -m "feat(api): add frame parser (CSV bytes → typed pandas DataFrames)

- ParsedFrames dataclass holds cycles/sleeps/workouts/journal
- String-first read with explicit dtype coercion per column
- Drops rows with NaT timestamps; raises NoDataError on empty cycles
- Optional files become empty DataFrames with the right columns
- 5 frame tests passing"
```

---

## Task 8: Time helpers and base metrics

**Files:**
- Create: `apps/api/app/analysis/__init__.py`
- Create: `apps/api/app/analysis/time_helpers.py`
- Create: `apps/api/app/analysis/metrics.py`
- Create: `apps/api/tests/analysis/__init__.py`
- Create: `apps/api/tests/analysis/test_time_helpers.py`
- Create: `apps/api/tests/analysis/test_metrics.py`

- [ ] **Step 1: Write time-helpers tests**

Create `apps/api/tests/analysis/__init__.py` (empty), then `apps/api/tests/analysis/test_time_helpers.py`:

```python
from datetime import datetime

import pytest

from app.analysis.time_helpers import bedtime_hour, format_clock, wake_hour


@pytest.mark.parametrize(
    ("dt", "expected"),
    [
        (datetime(2025, 1, 1, 23, 30), 23.5),
        (datetime(2025, 1, 2, 1, 0), 25.0),
        (datetime(2025, 1, 2, 4, 45), 28.75),
        (datetime(2025, 1, 1, 12, 0), 12.0),
    ],
)
def test_bedtime_hour(dt: datetime, expected: float) -> None:
    assert bedtime_hour(dt) == pytest.approx(expected)


def test_wake_hour() -> None:
    assert wake_hour(datetime(2025, 1, 2, 9, 30)) == pytest.approx(9.5)


@pytest.mark.parametrize(
    ("h", "expected"),
    [
        (23.5, "23:30"),
        (25.0, "01:00"),
        (28.75, "04:45"),
    ],
)
def test_format_clock(h: float, expected: str) -> None:
    assert format_clock(h) == expected
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/analysis/test_time_helpers.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement `analysis/__init__.py` and `time_helpers.py`**

Create `apps/api/app/analysis/__init__.py` (empty file).

Create `apps/api/app/analysis/time_helpers.py`:

```python
"""Time math used by sleep and trends analysis.

`bedtime_hour` maps an absolute datetime to a single number on a "day-aligned"
scale where 12:00–11:59 next day = 12.0–35.99. This makes "around midnight"
times statistically continuous instead of wrapping at 24.
"""
import math
from datetime import datetime


def bedtime_hour(dt: datetime) -> float:
    h = dt.hour + dt.minute / 60 + dt.second / 3600
    return h if h >= 12 else h + 24


def wake_hour(dt: datetime) -> float:
    return dt.hour + dt.minute / 60 + dt.second / 3600


def format_clock(h: float) -> str:
    h = h % 24
    hours = int(math.floor(h))
    minutes = int(round((h - hours) * 60))
    if minutes == 60:
        hours = (hours + 1) % 24
        minutes = 0
    return f"{hours:02d}:{minutes:02d}"
```

- [ ] **Step 4: Write the metrics test**

Create `apps/api/tests/analysis/test_metrics.py`:

```python
import pytest

from app.analysis.metrics import compute_metrics, compute_period
from app.parsing.frames import parse_frames
from app.parsing.zip_loader import load_zip
from tests.fixtures.build_fixtures import build_all_fixtures, fixtures_dir


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures() -> None:
    build_all_fixtures()


def _frames():
    return parse_frames(load_zip(fixtures_dir() / "happy.zip", max_bytes=50 * 1024 * 1024))


def test_compute_metrics_happy() -> None:
    f = _frames()
    m = compute_metrics(f)
    assert 50 <= m.hrv_ms <= 150
    assert 40 <= m.rhr_bpm <= 60
    assert 0 <= m.sleep_efficiency_pct <= 100
    assert m.sleep_debt_min >= 0


def test_compute_period_happy() -> None:
    f = _frames()
    p = compute_period(f)
    assert p.days == 60
    assert p.start.startswith("2025-01-01")
    assert p.end.startswith("2025-03-01")
```

- [ ] **Step 5: Run to confirm failure**

```bash
uv run pytest tests/analysis/test_metrics.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 6: Implement `analysis/metrics.py`**

Create `apps/api/app/analysis/metrics.py`:

```python
"""Top-level aggregate metrics computed from parsed frames."""
from app.models.report import Metrics, Period
from app.parsing.frames import ParsedFrames


def _safe_mean(series, default: float = 0.0) -> float:
    s = series.dropna()
    return float(s.mean()) if len(s) > 0 else default


def compute_period(f: ParsedFrames) -> Period:
    starts = f.cycles["Cycle start time"].dropna()
    if starts.empty:
        return Period(start="", end="", days=0)
    start = starts.min()
    end = starts.max()
    return Period(
        start=start.date().isoformat(),
        end=end.date().isoformat(),
        days=int((end.date() - start.date()).days) + 1,
    )


def compute_metrics(f: ParsedFrames) -> Metrics:
    c = f.cycles
    return Metrics(
        hrv_ms=_safe_mean(c["Heart rate variability (ms)"]),
        rhr_bpm=_safe_mean(c["Resting heart rate (bpm)"]),
        resp_rpm=_safe_mean(c["Respiratory rate (rpm)"]),
        spo2_pct=_safe_mean(c["Blood oxygen %"]),
        sleep_efficiency_pct=_safe_mean(c["Sleep efficiency %"]),
        sleep_consistency_pct=_safe_mean(c["Sleep consistency %"]),
        sleep_debt_min=_safe_mean(c["Sleep debt (min)"]),
    )
```

- [ ] **Step 7: Run all analysis tests**

```bash
uv run pytest tests/analysis/ -v
```

Expected: `7 passed` (4 time helpers + 2 metrics + 1 — adjust if your test count differs; the count should match the number of test functions in steps 1 and 4).

- [ ] **Step 8: Commit**

```bash
git add apps/api/
git commit -m "feat(api): add time helpers and base metrics

- bedtime_hour/wake_hour/format_clock for sleep analysis
- compute_metrics: HRV, RHR, resp, SpO2, sleep efficiency/consistency/debt
- compute_period: ISO date range from cycles
- Tests passing"
```

---

## Task 9: Trends and recovery section

**Files:**
- Create: `apps/api/app/analysis/trends.py`
- Create: `apps/api/tests/analysis/test_trends.py`

- [ ] **Step 1: Write trends tests**

Create `apps/api/tests/analysis/test_trends.py`:

```python
import pytest

from app.analysis.trends import (
    compute_dials,
    compute_recovery_section,
    compute_trends_section,
)
from app.parsing.frames import parse_frames
from app.parsing.zip_loader import load_zip
from tests.fixtures.build_fixtures import build_all_fixtures, fixtures_dir


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures() -> None:
    build_all_fixtures()


def _frames():
    return parse_frames(load_zip(fixtures_dir() / "happy.zip", max_bytes=50 * 1024 * 1024))


def test_compute_dials_shape() -> None:
    d = compute_dials(_frames())
    assert d.sleep.unit == "h"
    assert d.recovery.unit == "%"
    assert d.strain.unit == ""
    assert d.strain.label in ("light", "moderate", "high", "all_out")
    assert 0 <= d.recovery.value <= 100
    assert d.recovery.green_pct is not None
    assert d.sleep.performance_pct is not None


def test_recovery_section_shape() -> None:
    r = compute_recovery_section(_frames())
    assert len(r.trend) == 60
    assert len(r.by_dow) == 7
    assert {e.dow for e in r.by_dow} == {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
    assert (
        abs(r.distribution.green + r.distribution.yellow + r.distribution.red - 100.0)
        < 0.5
    )


def test_trends_section_shape() -> None:
    t = compute_trends_section(_frames())
    assert len(t.monthly) >= 1
    fl = t.first_vs_last_60d
    assert isinstance(fl.bedtime_h, tuple) and len(fl.bedtime_h) == 2
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/analysis/test_trends.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement `analysis/trends.py`**

Create `apps/api/app/analysis/trends.py`:

```python
"""Day-of-week, monthly, dial values, and trend comparisons."""
from typing import Literal

import pandas as pd

from app.models.report import (
    DialMetric,
    Dials,
    DowEntry,
    MonthlyAgg,
    RecoveryDistribution,
    RecoverySection,
    SickEpisode,
    TrendComparison,
    TrendPoint,
    TrendsSection,
)
from app.parsing.frames import ParsedFrames

DowName = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
_DOW_ORDER: tuple[DowName, ...] = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _strain_label(value: float) -> Literal["light", "moderate", "high", "all_out"]:
    if value < 10:
        return "light"
    if value < 14:
        return "moderate"
    if value < 18:
        return "high"
    return "all_out"


def compute_dials(f: ParsedFrames) -> Dials:
    c = f.cycles
    sleep_h_mean = float(c["Asleep duration (min)"].dropna().mean() / 60.0) if not c.empty else 0.0
    sleep_perf_mean = float(c["Sleep performance %"].dropna().mean()) if not c.empty else 0.0
    rec_mean = float(c["Recovery score %"].dropna().mean()) if not c.empty else 0.0
    rec_green_pct = float((c["Recovery score %"].dropna() >= 67).mean() * 100) if not c.empty else 0.0
    strain_mean = float(c["Day Strain"].dropna().mean()) if not c.empty else 0.0
    return Dials(
        sleep=DialMetric(value=round(sleep_h_mean, 2), unit="h", performance_pct=round(sleep_perf_mean, 1)),
        recovery=DialMetric(value=round(rec_mean, 1), unit="%", green_pct=round(rec_green_pct, 1)),
        strain=DialMetric(value=round(strain_mean, 1), unit="", label=_strain_label(strain_mean)),
    )


def compute_recovery_section(f: ParsedFrames) -> RecoverySection:
    c = f.cycles
    trend: list[TrendPoint] = []
    for _, row in c.iterrows():
        ts = row["Cycle start time"]
        if pd.isna(ts):
            continue
        v = row["Recovery score %"]
        trend.append(
            TrendPoint(date=ts.date().isoformat(), value=None if pd.isna(v) else float(v))
        )

    dow_series = c["Cycle start time"].dt.day_name().str.lower().str[:3]
    by_dow_records: list[DowEntry] = []
    for dow in _DOW_ORDER:
        sub = c[dow_series == dow]
        rec = sub["Recovery score %"].dropna()
        by_dow_records.append(
            DowEntry(dow=dow, mean=round(float(rec.mean() if len(rec) else 0.0), 1), n=int(len(rec)))
        )

    rec = c["Recovery score %"].dropna()
    n = max(len(rec), 1)
    distribution = RecoveryDistribution(
        green=round(float((rec >= 67).sum()) / n * 100, 1),
        yellow=round(float(((rec >= 34) & (rec < 67)).sum()) / n * 100, 1),
        red=round(float((rec < 34).sum()) / n * 100, 1),
    )

    sick_episodes: list[SickEpisode] = []
    if not rec.empty:
        hrv_med = float(c["Heart rate variability (ms)"].median())
        rhr_med = float(c["Resting heart rate (bpm)"].median())
        mask = (
            (c["Recovery score %"] < 30)
            & (c["Heart rate variability (ms)"] < hrv_med * 0.7)
            & (c["Resting heart rate (bpm)"] > rhr_med * 1.15)
        )
        for _, row in c[mask].iterrows():
            sick_episodes.append(
                SickEpisode(
                    date=row["Cycle start time"].date().isoformat(),
                    recovery=float(row["Recovery score %"]),
                    rhr=float(row["Resting heart rate (bpm)"]),
                    hrv=float(row["Heart rate variability (ms)"]),
                    skin_temp_c=None
                    if pd.isna(row["Skin temp (celsius)"])
                    else float(row["Skin temp (celsius)"]),
                )
            )

    return RecoverySection(
        trend=trend,
        by_dow=by_dow_records,
        distribution=distribution,
        sick_episodes=sick_episodes,
    )


def compute_trends_section(f: ParsedFrames) -> TrendsSection:
    c = f.cycles.copy()
    c["__month"] = c["Cycle start time"].dt.strftime("%Y-%m")
    monthly_records: list[MonthlyAgg] = []
    for month, sub in c.groupby("__month"):
        monthly_records.append(
            MonthlyAgg(
                month=str(month),
                recovery=round(float(sub["Recovery score %"].dropna().mean() or 0.0), 1),
                hrv=round(float(sub["Heart rate variability (ms)"].dropna().mean() or 0.0), 1),
                rhr=round(float(sub["Resting heart rate (bpm)"].dropna().mean() or 0.0), 1),
                sleep_h=round(
                    float((sub["Asleep duration (min)"].dropna() / 60).mean() or 0.0), 2
                ),
            )
        )

    first = c.head(60)
    last = c.tail(60)

    def _bed_h(df: pd.DataFrame) -> float:
        from app.analysis.time_helpers import bedtime_hour
        vals = [bedtime_hour(t) for t in df["Sleep onset"].dropna()]
        return round(sum(vals) / len(vals), 2) if vals else 0.0

    def _sleep_h(df: pd.DataFrame) -> float:
        s = df["Asleep duration (min)"].dropna() / 60
        return round(float(s.mean()) if len(s) else 0.0, 2)

    def _rhr(df: pd.DataFrame) -> float:
        s = df["Resting heart rate (bpm)"].dropna()
        return round(float(s.mean()) if len(s) else 0.0, 1)

    cmp = TrendComparison(
        bedtime_h=(_bed_h(first), _bed_h(last)),
        sleep_h=(_sleep_h(first), _sleep_h(last)),
        rhr=(_rhr(first), _rhr(last)),
        workouts=(0, 0),  # filled in by strain.py downstream if needed
    )

    return TrendsSection(monthly=monthly_records, first_vs_last_60d=cmp)
```

- [ ] **Step 4: Run trends tests**

```bash
uv run pytest tests/analysis/test_trends.py -v
```

Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add apps/api/
git commit -m "feat(api): add dials, recovery section, and trends section

- compute_dials: sleep/recovery/strain dial values + green_pct + strain label
- compute_recovery_section: full daily trend, dow breakdown, distribution, sick_episodes
- compute_trends_section: monthly aggregates + first-60-vs-last-60 comparison
- 3 trends tests passing"
```

---

## Task 10: Sleep section

**Files:**
- Create: `apps/api/app/analysis/sleep.py`
- Create: `apps/api/tests/analysis/test_sleep.py`

- [ ] **Step 1: Write sleep tests**

Create `apps/api/tests/analysis/test_sleep.py`:

```python
import pytest

from app.analysis.sleep import compute_sleep_section
from app.parsing.frames import parse_frames
from app.parsing.zip_loader import load_zip
from tests.fixtures.build_fixtures import build_all_fixtures, fixtures_dir


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures() -> None:
    build_all_fixtures()


def _frames():
    return parse_frames(load_zip(fixtures_dir() / "happy.zip", max_bytes=50 * 1024 * 1024))


def test_sleep_section_basics() -> None:
    s = compute_sleep_section(_frames())
    # bedtime/wake clock formats
    assert ":" in s.avg_bedtime
    assert ":" in s.avg_wake
    assert s.bedtime_std_h >= 0
    # stage percentages roughly sum to 100
    total = s.stage_pct.light + s.stage_pct.rem + s.stage_pct.deep
    assert 80 <= total <= 100  # remainder is awake/error
    # consistency strip = last 14 days
    assert len(s.consistency_strip) <= 14
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/analysis/test_sleep.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement `analysis/sleep.py`**

Create `apps/api/app/analysis/sleep.py`:

```python
"""Sleep section: average bedtime/wake, stage percentages, hypnogram, consistency strip."""
import math

import pandas as pd

from app.analysis.time_helpers import bedtime_hour, format_clock, wake_hour
from app.models.report import (
    BedtimeStrip,
    SleepDurations,
    SleepSection,
    SleepStagePct,
)
from app.parsing.frames import ParsedFrames


def compute_sleep_section(f: ParsedFrames) -> SleepSection:
    c = f.cycles
    bed_hours = [bedtime_hour(t) for t in c["Sleep onset"].dropna()]
    wake_hours = [wake_hour(t) for t in c["Wake onset"].dropna()]
    avg_bed = sum(bed_hours) / len(bed_hours) if bed_hours else 0.0
    avg_wake = sum(wake_hours) / len(wake_hours) if wake_hours else 0.0

    if len(bed_hours) >= 2:
        mean = sum(bed_hours) / len(bed_hours)
        var = sum((x - mean) ** 2 for x in bed_hours) / (len(bed_hours) - 1)
        bed_std = math.sqrt(var)
    else:
        bed_std = 0.0

    light = float(c["Light sleep duration (min)"].dropna().mean() or 0.0)
    rem = float(c["REM duration (min)"].dropna().mean() or 0.0)
    deep = float(c["Deep (SWS) duration (min)"].dropna().mean() or 0.0)
    awake = float(c["Awake duration (min)"].dropna().mean() or 0.0)
    asleep_total = light + rem + deep
    if asleep_total > 0:
        light_pct = round(light / asleep_total * 100, 1)
        rem_pct = round(rem / asleep_total * 100, 1)
        deep_pct = round(deep / asleep_total * 100, 1)
    else:
        light_pct = rem_pct = deep_pct = 0.0

    last14 = c.tail(14)
    strip: list[BedtimeStrip] = []
    for _, row in last14.iterrows():
        if pd.isna(row["Sleep onset"]) or pd.isna(row["Wake onset"]):
            continue
        strip.append(
            BedtimeStrip(
                date=row["Cycle start time"].date().isoformat(),
                bed_local=format_clock(bedtime_hour(row["Sleep onset"])),
                wake_local=format_clock(wake_hour(row["Wake onset"])),
            )
        )

    return SleepSection(
        avg_bedtime=format_clock(avg_bed),
        avg_wake=format_clock(avg_wake),
        bedtime_std_h=round(bed_std, 2),
        avg_durations=SleepDurations(
            light_min=round(light, 1),
            rem_min=round(rem, 1),
            deep_min=round(deep, 1),
            awake_min=round(awake, 1),
        ),
        stage_pct=SleepStagePct(light=light_pct, rem=rem_pct, deep=deep_pct),
        hypnogram_sample=None,  # v1: skip; needs per-night stage timeline data
        consistency_strip=strip,
    )
```

- [ ] **Step 4: Run sleep tests**

```bash
uv run pytest tests/analysis/test_sleep.py -v
```

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add apps/api/
git commit -m "feat(api): add sleep section

- avg bedtime/wake (clock format, day-aligned hour math)
- bedtime std (sample stddev)
- stage durations + percentages (light/rem/deep)
- 14-day bedtime consistency strip
- hypnogram_sample left None for v1 (no per-night stage timeline in CSV)"
```

---

## Task 11: Strain and workouts section

**Files:**
- Create: `apps/api/app/analysis/strain.py`
- Create: `apps/api/tests/analysis/test_strain.py`

- [ ] **Step 1: Write strain tests**

Create `apps/api/tests/analysis/test_strain.py`:

```python
import pytest

from app.analysis.strain import compute_strain_section, compute_workouts_section
from app.parsing.frames import parse_frames
from app.parsing.zip_loader import load_zip
from tests.fixtures.build_fixtures import build_all_fixtures, fixtures_dir


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures() -> None:
    build_all_fixtures()


def _happy():
    return parse_frames(load_zip(fixtures_dir() / "happy.zip", max_bytes=50 * 1024 * 1024))


def _no_workouts():
    return parse_frames(
        load_zip(fixtures_dir() / "no_workouts.zip", max_bytes=50 * 1024 * 1024)
    )


def test_strain_section_basics() -> None:
    s = compute_strain_section(_happy())
    assert 0 <= s.avg_strain <= 21
    total = (
        s.distribution.light
        + s.distribution.moderate
        + s.distribution.high
        + s.distribution.all_out
    )
    assert abs(total - 100.0) < 0.5
    assert len(s.trend) > 0


def test_workouts_section_present_when_data() -> None:
    w = compute_workouts_section(_happy())
    assert w is not None
    assert w.total > 0
    assert any(a.name == "Walking" for a in w.by_activity)


def test_workouts_section_none_when_empty() -> None:
    w = compute_workouts_section(_no_workouts())
    assert w is None
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/analysis/test_strain.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement `analysis/strain.py`**

Create `apps/api/app/analysis/strain.py`:

```python
"""Strain section + workouts section."""
import pandas as pd

from app.models.report import (
    ActivityAgg,
    StrainDistribution,
    StrainSection,
    TopStrainDay,
    TrendPoint,
    WorkoutsSection,
)
from app.parsing.frames import ParsedFrames


def compute_strain_section(f: ParsedFrames) -> StrainSection:
    c = f.cycles
    strains = c["Day Strain"].dropna()
    n = max(len(strains), 1)
    dist = StrainDistribution(
        light=round(float((strains < 10).sum()) / n * 100, 1),
        moderate=round(float(((strains >= 10) & (strains < 14)).sum()) / n * 100, 1),
        high=round(float(((strains >= 14) & (strains < 18)).sum()) / n * 100, 1),
        all_out=round(float((strains >= 18).sum()) / n * 100, 1),
    )

    trend: list[TrendPoint] = []
    for _, row in c.iterrows():
        ts = row["Cycle start time"]
        if pd.isna(ts):
            continue
        v = row["Day Strain"]
        trend.append(
            TrendPoint(date=ts.date().isoformat(), value=None if pd.isna(v) else float(v))
        )

    return StrainSection(
        avg_strain=round(float(strains.mean() or 0.0), 1),
        distribution=dist,
        trend=trend,
    )


def compute_workouts_section(f: ParsedFrames) -> WorkoutsSection | None:
    w = f.workouts
    if w.empty:
        return None

    by_activity_records: list[ActivityAgg] = []
    total_strain_all = float(w["Activity Strain"].dropna().sum() or 0.0)
    for activity, sub in w.groupby("Activity name"):
        total_strain = float(sub["Activity Strain"].dropna().sum() or 0.0)
        by_activity_records.append(
            ActivityAgg(
                name=str(activity),
                count=int(len(sub)),
                total_strain=round(total_strain, 1),
                total_min=round(float(sub["Duration (min)"].dropna().sum() or 0.0), 1),
                pct_of_total_strain=round(
                    total_strain / total_strain_all * 100 if total_strain_all > 0 else 0.0,
                    1,
                ),
            )
        )
    by_activity_records.sort(key=lambda a: a.total_strain, reverse=True)

    c = f.cycles.sort_values("Cycle start time").reset_index(drop=True)
    top_records: list[TopStrainDay] = []
    top10 = c.nlargest(10, "Day Strain")
    for idx, row in top10.iterrows():
        next_row = c.iloc[idx + 1] if idx + 1 < len(c) else None
        next_recovery = (
            float(next_row["Recovery score %"])
            if next_row is not None and not pd.isna(next_row["Recovery score %"])
            else None
        )
        top_records.append(
            TopStrainDay(
                date=row["Cycle start time"].date().isoformat(),
                day_strain=round(float(row["Day Strain"]), 1),
                recovery=float(row["Recovery score %"])
                if not pd.isna(row["Recovery score %"])
                else 0.0,
                next_recovery=next_recovery,
            )
        )

    return WorkoutsSection(
        total=int(len(w)),
        by_activity=by_activity_records,
        top_strain_days=top_records,
    )
```

- [ ] **Step 4: Run strain tests**

```bash
uv run pytest tests/analysis/test_strain.py -v
```

Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add apps/api/
git commit -m "feat(api): add strain and workouts sections

- compute_strain_section: avg, distribution by category, daily trend
- compute_workouts_section: by-activity rollup, top-10 strain days w/ next-day recovery
- Returns None for empty workouts (signals 'hide section' to frontend)
- 3 strain tests passing"
```

---

## Task 12: Insights framework + 3 sleep-related rules

**Files:**
- Create: `apps/api/app/analysis/insights.py`
- Create: `apps/api/tests/analysis/test_insights.py`

- [ ] **Step 1: Write tests for the framework + first 3 rules**

Create `apps/api/tests/analysis/test_insights.py`:

```python
import pandas as pd
import pytest

from app.analysis.insights import (
    INSIGHT_RULES,
    insight_bedtime_consistency,
    insight_late_chronotype,
    insight_undersleep,
    run_insight_rules,
)
from app.parsing.frames import parse_frames
from app.parsing.zip_loader import load_zip
from tests.fixtures.build_fixtures import build_all_fixtures, fixtures_dir


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures() -> None:
    build_all_fixtures()


def _happy_frames():
    return parse_frames(load_zip(fixtures_dir() / "happy.zip", max_bytes=50 * 1024 * 1024))


def test_insight_undersleep_triggers() -> None:
    f = _happy_frames()
    # Force most nights under 6h
    f.cycles.loc[:, "Asleep duration (min)"] = 300.0
    f.cycles.loc[:, "Recovery score %"] = 50.0
    insight = insight_undersleep(f)
    assert insight is not None
    assert insight.kind == "undersleep"
    assert insight.severity in ("medium", "high")


def test_insight_undersleep_skipped_when_rare() -> None:
    f = _happy_frames()
    f.cycles.loc[:, "Asleep duration (min)"] = 480.0  # 8h, no undersleep
    insight = insight_undersleep(f)
    assert insight is None


def test_insight_bedtime_consistency_triggers() -> None:
    f = _happy_frames()
    # Make bedtime alternate by 4 hours so std is large
    onsets = pd.to_datetime(
        ["2025-01-01 23:00", "2025-01-02 03:00"] * 30 + ["2025-01-31 23:00"]
    )
    f.cycles["Sleep onset"] = onsets[: len(f.cycles)]
    f.cycles.loc[:, "Recovery score %"] = 60.0
    insight = insight_bedtime_consistency(f)
    assert insight is not None
    assert insight.kind == "bedtime_consistency"


def test_insight_late_chronotype_triggers() -> None:
    f = _happy_frames()
    onsets = pd.to_datetime(
        [f"2025-01-{d:02d} 02:30" for d in range(1, len(f.cycles) + 1)]
    )
    f.cycles["Sleep onset"] = onsets
    insight = insight_late_chronotype(f)
    assert insight is not None
    assert insight.kind == "late_chronotype"


def test_insight_rules_list_contains_10() -> None:
    assert len(INSIGHT_RULES) == 10


def test_run_insight_rules_returns_only_triggered() -> None:
    f = _happy_frames()
    f.cycles.loc[:, "Asleep duration (min)"] = 300.0
    f.cycles.loc[:, "Recovery score %"] = 40.0
    results = run_insight_rules(f)
    assert all(r is not None for r in results)
    kinds = {r.kind for r in results}
    assert "undersleep" in kinds
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/analysis/test_insights.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement `analysis/insights.py` (framework + 3 rules)**

Create `apps/api/app/analysis/insights.py`:

```python
"""Insight rules.

Each rule is a pure function `(ParsedFrames) -> Insight | None`.
Returning None means the rule didn't trigger and is dropped from the response.
"""
from collections.abc import Callable

from app.analysis.time_helpers import bedtime_hour
from app.models.insight import Insight, InsightHighlight
from app.parsing.frames import ParsedFrames

InsightFn = Callable[[ParsedFrames], Insight | None]


def insight_undersleep(f: ParsedFrames) -> Insight | None:
    sleep_h = f.cycles["Asleep duration (min)"].dropna() / 60
    if sleep_h.empty:
        return None
    short_pct = float((sleep_h < 6).mean())
    if short_pct < 0.05:
        return None
    rec = f.cycles["Recovery score %"]
    short_mask = (sleep_h < 6).reindex(f.cycles.index, fill_value=False)
    long_mask = (sleep_h >= 8).reindex(f.cycles.index, fill_value=False)
    rec_short = float(rec[short_mask].dropna().mean() or 0.0)
    rec_long = float(rec[long_mask].dropna().mean() or 0.0)
    delta = round(rec_long - rec_short)
    severity = "high" if short_pct > 0.15 else "medium"
    return Insight(
        kind="undersleep",
        severity=severity,
        title=f"You undersleep {round(short_pct * 100)}% of nights",
        body=(
            f"On nights under 6 hours your recovery averages {round(rec_short)}%; "
            f"on nights with 8+ hours it averages {round(rec_long)}%. "
            f"Adding sleep is your single biggest lever."
        ),
        highlight=InsightHighlight(value=f"+{delta}", unit="pp"),
    )


def insight_bedtime_consistency(f: ParsedFrames) -> Insight | None:
    onsets = f.cycles["Sleep onset"].dropna()
    if len(onsets) < 14:
        return None
    bed_h = onsets.apply(bedtime_hour)
    rolling_std = bed_h.rolling(7, min_periods=4).std().dropna()
    if rolling_std.empty:
        return None
    rec = f.cycles["Recovery score %"]
    low_var_mask = (rolling_std < 1).reindex(rec.index, fill_value=False)
    high_var_mask = (rolling_std > 3).reindex(rec.index, fill_value=False)
    rec_low_var = float(rec[low_var_mask].dropna().mean() or 0.0)
    rec_high_var = float(rec[high_var_mask].dropna().mean() or 0.0)
    delta = round(rec_low_var - rec_high_var)
    if delta < 5 or rec_low_var == 0 or rec_high_var == 0:
        return None
    return Insight(
        kind="bedtime_consistency",
        severity="medium",
        title="Your most stable weeks score much higher",
        body=(
            f"Weeks with bedtime variance under 1h average {round(rec_low_var)}% recovery; "
            f"weeks over 3h variance average {round(rec_high_var)}%. "
            f"Going to bed at a similar time pays off as much as sleeping more."
        ),
        highlight=InsightHighlight(value=f"+{delta}", unit="pp"),
    )


def insight_late_chronotype(f: ParsedFrames) -> Insight | None:
    onsets = f.cycles["Sleep onset"].dropna()
    if len(onsets) < 14:
        return None
    bed_h = [bedtime_hour(t) for t in onsets]
    avg_bed = sum(bed_h) / len(bed_h)
    if avg_bed < 25.0:  # earlier than 01:00
        return None
    return Insight(
        kind="late_chronotype",
        severity="low",
        title="You're a strong night owl",
        body=(
            f"Your average bedtime is past 01:00. Even with the same total sleep, "
            f"earlier bedtimes (00:00–01:00) tend to score 5-10 percentage points "
            f"higher in recovery."
        ),
        highlight=InsightHighlight(value="01:00+"),
    )


# Stubs to be filled in subsequent tasks (Tasks 13-14)
def insight_overtraining(f: ParsedFrames) -> Insight | None:
    return None


def insight_sick_episodes(f: ParsedFrames) -> Insight | None:
    return None


def insight_travel_impact(f: ParsedFrames) -> Insight | None:
    return None


def insight_dow_pattern(f: ParsedFrames) -> Insight | None:
    return None


def insight_sleep_stage_quality(f: ParsedFrames) -> Insight | None:
    return None


def insight_long_term_trend(f: ParsedFrames) -> Insight | None:
    return None


def insight_workout_mix(f: ParsedFrames) -> Insight | None:
    return None


INSIGHT_RULES: list[InsightFn] = [
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


def run_insight_rules(f: ParsedFrames) -> list[Insight]:
    results: list[Insight] = []
    for rule in INSIGHT_RULES:
        out = rule(f)
        if out is not None:
            results.append(out)
    return results
```

- [ ] **Step 4: Run the insight tests**

```bash
uv run pytest tests/analysis/test_insights.py -v
```

Expected: `6 passed`.

- [ ] **Step 5: Commit**

```bash
git add apps/api/
git commit -m "feat(api): add insights framework + 3 sleep rules

- InsightFn = (ParsedFrames) -> Insight | None
- run_insight_rules() iterates INSIGHT_RULES, drops None
- insight_undersleep: triggers when >5% of nights <6h
- insight_bedtime_consistency: 7d rolling std, low-var vs high-var weeks
- insight_late_chronotype: avg bedtime past 01:00
- 7 stub rules for Tasks 13-14"
```

---

## Task 13: Insights — overtraining, sick_episodes, travel_impact

**Files:**
- Modify: `apps/api/app/analysis/insights.py`
- Modify: `apps/api/tests/analysis/test_insights.py`

- [ ] **Step 1: Add tests for the next 3 rules**

Append to `apps/api/tests/analysis/test_insights.py`:

```python
def test_insight_overtraining_triggers() -> None:
    f = _happy_frames()
    f.cycles.loc[:, "Day Strain"] = 16.0  # everything is strenuous
    f.cycles.loc[:, "Recovery score %"] = 50.0
    from app.analysis.insights import insight_overtraining
    insight = insight_overtraining(f)
    assert insight is not None
    assert insight.kind == "overtraining"


def test_insight_sick_episodes_triggers() -> None:
    f = _happy_frames()
    f.cycles.loc[f.cycles.index[0], "Recovery score %"] = 5.0
    f.cycles.loc[f.cycles.index[0], "Heart rate variability (ms)"] = 40.0
    f.cycles.loc[f.cycles.index[0], "Resting heart rate (bpm)"] = 80.0
    from app.analysis.insights import insight_sick_episodes
    insight = insight_sick_episodes(f)
    assert insight is not None
    assert insight.kind == "sick_episodes"


def test_insight_travel_impact_triggers() -> None:
    f = _happy_frames()
    f.cycles.loc[:5, "Cycle timezone"] = "UTC+08:00"
    f.cycles.loc[:5, "Recovery score %"] = 50.0
    f.cycles.loc[6:, "Cycle timezone"] = "UTC+05:00"
    f.cycles.loc[6:, "Recovery score %"] = 80.0
    from app.analysis.insights import insight_travel_impact
    insight = insight_travel_impact(f)
    assert insight is not None
    assert insight.kind == "travel_impact"
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/analysis/test_insights.py::test_insight_overtraining_triggers -v
```

Expected: assertion error (the stub returns None).

- [ ] **Step 3: Implement the 3 rules**

In `apps/api/app/analysis/insights.py`, replace the three stub functions (`insight_overtraining`, `insight_sick_episodes`, `insight_travel_impact`) with:

```python
def insight_overtraining(f: ParsedFrames) -> Insight | None:
    c = f.cycles.sort_values("Cycle start time").reset_index(drop=True)
    if len(c) < 5:
        return None
    high_strain_idx = c.index[c["Day Strain"] > 15].tolist()
    if not high_strain_idx:
        return None
    next_recoveries = []
    for i in high_strain_idx:
        if i + 1 < len(c):
            v = c.loc[i + 1, "Recovery score %"]
            if not (v is None):
                next_recoveries.append(float(v))
    if not next_recoveries:
        return None
    baseline = float(c["Recovery score %"].dropna().mean() or 0.0)
    after = sum(next_recoveries) / len(next_recoveries)
    delta = baseline - after
    if delta < 5:
        return None
    return Insight(
        kind="overtraining",
        severity="medium",
        title="Big strain days drag the next day",
        body=(
            f"After days with strain over 15, your recovery the next morning averages "
            f"{round(after)}% — about {round(delta)} points below your usual baseline of {round(baseline)}%. "
            f"Consider a recovery day after strenuous efforts."
        ),
        highlight=InsightHighlight(value=f"-{round(delta)}", unit="pp"),
    )


def insight_sick_episodes(f: ParsedFrames) -> Insight | None:
    c = f.cycles
    if c["Recovery score %"].dropna().empty:
        return None
    hrv_med = float(c["Heart rate variability (ms)"].median())
    rhr_med = float(c["Resting heart rate (bpm)"].median())
    mask = (
        (c["Recovery score %"] < 30)
        & (c["Heart rate variability (ms)"] < hrv_med * 0.7)
        & (c["Resting heart rate (bpm)"] > rhr_med * 1.15)
    )
    n = int(mask.sum())
    if n == 0:
        return None
    return Insight(
        kind="sick_episodes",
        severity="low",
        title=f"{n} likely illness day{'s' if n > 1 else ''} detected",
        body=(
            "On these days HRV crashed, resting heart rate spiked, and recovery dropped "
            "below 30 — typical signs your body is fighting something. Rest is the right "
            "call."
        ),
        highlight=InsightHighlight(value=str(n)),
    )


def insight_travel_impact(f: ParsedFrames) -> Insight | None:
    c = f.cycles
    tzs = c["Cycle timezone"].dropna()
    if tzs.empty:
        return None
    home_tz = tzs.value_counts().idxmax()
    away_mask = c["Cycle timezone"] != home_tz
    if away_mask.sum() < 3:
        return None
    rec_home = float(c.loc[~away_mask, "Recovery score %"].dropna().mean() or 0.0)
    rec_away = float(c.loc[away_mask, "Recovery score %"].dropna().mean() or 0.0)
    delta = rec_home - rec_away
    if delta < 3:
        return None
    return Insight(
        kind="travel_impact",
        severity="medium",
        title="Travel hits your recovery",
        body=(
            f"You spent {int(away_mask.sum())} days outside your home timezone "
            f"({home_tz}). Recovery dropped from {round(rec_home)}% at home to "
            f"{round(rec_away)}% on the road."
        ),
        highlight=InsightHighlight(value=f"-{round(delta)}", unit="pp"),
    )
```

- [ ] **Step 4: Run insight tests**

```bash
uv run pytest tests/analysis/test_insights.py -v
```

Expected: `9 passed`.

- [ ] **Step 5: Commit**

```bash
git add apps/api/
git commit -m "feat(api): add overtraining/sick_episodes/travel_impact insights

- overtraining: next-day recovery after strain >15 vs baseline
- sick_episodes: HRV crash + RHR spike + recovery <30
- travel_impact: home tz vs away tz recovery delta
- 9 insight tests passing"
```

---

## Task 14: Insights — dow_pattern, sleep_stage_quality, long_term_trend, workout_mix

**Files:**
- Modify: `apps/api/app/analysis/insights.py`
- Modify: `apps/api/tests/analysis/test_insights.py`

- [ ] **Step 1: Add tests for the last 4 rules**

Append to `apps/api/tests/analysis/test_insights.py`:

```python
def test_insight_dow_pattern_triggers() -> None:
    f = _happy_frames()
    # Make Wednesdays much worse
    dow = f.cycles["Cycle start time"].dt.day_name()
    f.cycles.loc[dow == "Wednesday", "Recovery score %"] = 40.0
    f.cycles.loc[dow != "Wednesday", "Recovery score %"] = 75.0
    from app.analysis.insights import insight_dow_pattern
    insight = insight_dow_pattern(f)
    assert insight is not None
    assert insight.kind == "dow_pattern"
    assert "wed" in insight.body.lower() or "wednesday" in insight.body.lower()


def test_insight_sleep_stage_quality_triggers() -> None:
    f = _happy_frames()
    # Force >20% deep sleep
    f.cycles.loc[:, "Light sleep duration (min)"] = 200.0
    f.cycles.loc[:, "REM duration (min)"] = 100.0
    f.cycles.loc[:, "Deep (SWS) duration (min)"] = 200.0
    from app.analysis.insights import insight_sleep_stage_quality
    insight = insight_sleep_stage_quality(f)
    assert insight is not None
    assert insight.kind == "sleep_stage_quality"


def test_insight_workout_mix_triggers() -> None:
    f = _happy_frames()
    # All workouts are Walking already (the fixture defaults), so the rule should fire
    from app.analysis.insights import insight_workout_mix
    insight = insight_workout_mix(f)
    assert insight is not None
    assert insight.kind == "workout_mix"
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/analysis/test_insights.py -v
```

Expected: 3 new tests fail (stubs).

- [ ] **Step 3: Replace the four remaining stubs**

In `apps/api/app/analysis/insights.py`, replace `insight_dow_pattern`, `insight_sleep_stage_quality`, `insight_long_term_trend`, and `insight_workout_mix` with:

```python
def insight_dow_pattern(f: ParsedFrames) -> Insight | None:
    c = f.cycles
    rec = c["Recovery score %"].dropna()
    if rec.empty:
        return None
    dow = c.loc[rec.index, "Cycle start time"].dt.day_name()
    by_dow = rec.groupby(dow).mean()
    if by_dow.empty:
        return None
    best_day = by_dow.idxmax()
    worst_day = by_dow.idxmin()
    spread = float(by_dow.max() - by_dow.min())
    if spread < 5:
        return None
    return Insight(
        kind="dow_pattern",
        severity="low",
        title=f"{worst_day} is your weakest day",
        body=(
            f"Your average recovery on {worst_day}s is {round(float(by_dow[worst_day]))}%, "
            f"versus {round(float(by_dow[best_day]))}% on {best_day}s. "
            f"Worth noticing what's different about that part of your week."
        ),
        highlight=InsightHighlight(value=f"-{round(spread)}", unit="pp"),
    )


def insight_sleep_stage_quality(f: ParsedFrames) -> Insight | None:
    c = f.cycles
    light = float(c["Light sleep duration (min)"].dropna().mean() or 0.0)
    rem = float(c["REM duration (min)"].dropna().mean() or 0.0)
    deep = float(c["Deep (SWS) duration (min)"].dropna().mean() or 0.0)
    total = light + rem + deep
    if total == 0:
        return None
    deep_pct = deep / total * 100
    rem_pct = rem / total * 100
    if max(deep_pct, rem_pct) < 20:
        return None
    return Insight(
        kind="sleep_stage_quality",
        severity="low",
        title="Your sleep architecture is excellent",
        body=(
            f"Average deep sleep is {round(deep_pct)}% and REM is {round(rem_pct)}% of "
            f"total sleep — both above typical adult baselines (around 13–18% for deep). "
            f"Your body is doing the recovery work it should."
        ),
        highlight=InsightHighlight(value=f"{round(deep_pct)}%", unit="deep"),
    )


def insight_long_term_trend(f: ParsedFrames) -> Insight | None:
    c = f.cycles.sort_values("Cycle start time").reset_index(drop=True)
    if len(c) < 120:
        return None
    first = c.head(60)
    last = c.tail(60)

    def _mean(df, col: str) -> float:
        return float(df[col].dropna().mean() or 0.0)

    rhr_delta = _mean(first, "Resting heart rate (bpm)") - _mean(
        last, "Resting heart rate (bpm)"
    )
    sleep_delta = (
        _mean(last, "Asleep duration (min)") - _mean(first, "Asleep duration (min)")
    ) / 60
    rec_delta = _mean(last, "Recovery score %") - _mean(first, "Recovery score %")
    improvements = sum(
        1
        for v in (rhr_delta, sleep_delta, rec_delta)
        if v > 0
    )
    if improvements < 2:
        return None
    return Insight(
        kind="long_term_trend",
        severity="low",
        title="You're trending in the right direction",
        body=(
            f"Comparing your first 60 days to your last 60: resting HR is "
            f"{abs(round(rhr_delta, 1))} bpm {'lower' if rhr_delta > 0 else 'higher'}, "
            f"average sleep is {abs(round(sleep_delta, 1))}h "
            f"{'longer' if sleep_delta > 0 else 'shorter'}, and recovery is "
            f"{abs(round(rec_delta))} pp {'higher' if rec_delta > 0 else 'lower'}."
        ),
        highlight=InsightHighlight(value=f"+{round(rec_delta)}", unit="pp"),
    )


def insight_workout_mix(f: ParsedFrames) -> Insight | None:
    if f.workouts.empty:
        return None
    total = float(f.workouts["Activity Strain"].dropna().sum() or 0.0)
    if total == 0:
        return None
    walking_strain = float(
        f.workouts.loc[
            f.workouts["Activity name"].isin(["Walking", "Activity"]), "Activity Strain"
        ]
        .dropna()
        .sum()
        or 0.0
    )
    pct = walking_strain / total * 100
    if pct < 50:
        return None
    return Insight(
        kind="workout_mix",
        severity="low",
        title="Most of your strain is steady-state",
        body=(
            f"Walking and general activity make up {round(pct)}% of your total strain. "
            f"Adding even one or two strength or interval sessions per week would diversify "
            f"the load."
        ),
        highlight=InsightHighlight(value=f"{round(pct)}%"),
    )
```

- [ ] **Step 4: Run all insight tests**

```bash
uv run pytest tests/analysis/test_insights.py -v
```

Expected: `12 passed`.

- [ ] **Step 5: Commit**

```bash
git add apps/api/
git commit -m "feat(api): add 4 final insight rules

- dow_pattern: worst vs best day-of-week recovery
- sleep_stage_quality: deep% or rem% above 20%
- long_term_trend: first-60d vs last-60d improvements (needs >=120 days)
- workout_mix: walking + activity >50% of total strain
- 12 insight tests passing"
```

---

## Task 15: Pipeline + snapshot test

**Files:**
- Create: `apps/api/app/analysis/pipeline.py`
- Create: `apps/api/tests/analysis/test_pipeline.py`
- Create: `apps/api/tests/snapshots/.gitkeep`

- [ ] **Step 1: Implement the pipeline**

Create `apps/api/app/analysis/pipeline.py`:

```python
"""Orchestrate parsed frames → WhoopReport."""
from app.analysis.insights import run_insight_rules
from app.analysis.metrics import compute_metrics, compute_period
from app.analysis.sleep import compute_sleep_section
from app.analysis.strain import compute_strain_section, compute_workouts_section
from app.analysis.trends import (
    compute_dials,
    compute_recovery_section,
    compute_trends_section,
)
from app.models.report import JournalSection, WhoopReport
from app.parsing.frames import ParsedFrames


def _compute_journal_section(f: ParsedFrames) -> JournalSection | None:
    j = f.journal
    if j.empty:
        return None
    days = j["Cycle start time"].nunique()
    questions: list = []
    for q, sub in j.groupby("Question text"):
        yes = int((sub["Answered yes"] == "true").sum())
        no = int((sub["Answered yes"] == "false").sum())
        questions.append(
            {
                "question": str(q),
                "yes": yes,
                "no": no,
                "mean_rec_yes": None,
                "mean_rec_no": None,
            }
        )
    note = (
        f"{int(days)} days logged. "
        + ("Sample too small for statistical conclusions." if days < 30 else "")
    ).strip()
    return JournalSection.model_validate(
        {"days_logged": int(days), "questions": questions, "note": note}
    )


def build_report(f: ParsedFrames) -> WhoopReport:
    return WhoopReport(
        schema_version=1,
        period=compute_period(f),
        dials=compute_dials(f),
        metrics=compute_metrics(f),
        recovery=compute_recovery_section(f),
        sleep=compute_sleep_section(f),
        strain=compute_strain_section(f),
        workouts=compute_workouts_section(f),
        journal=_compute_journal_section(f),
        trends=compute_trends_section(f),
        insights=run_insight_rules(f),
    )
```

- [ ] **Step 2: Write the snapshot test**

Create `apps/api/tests/snapshots/.gitkeep` (empty).

Create `apps/api/tests/analysis/test_pipeline.py`:

```python
import json
from pathlib import Path

import pytest

from app.analysis.pipeline import build_report
from app.parsing.frames import parse_frames
from app.parsing.zip_loader import load_zip
from tests.fixtures.build_fixtures import build_all_fixtures, fixtures_dir

SNAPSHOT_PATH = Path(__file__).parent.parent / "snapshots" / "happy_report.json"


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures() -> None:
    build_all_fixtures()


def _serialized_report() -> dict:
    f = parse_frames(load_zip(fixtures_dir() / "happy.zip", max_bytes=50 * 1024 * 1024))
    report = build_report(f)
    return json.loads(report.model_dump_json(by_alias=True))


def test_pipeline_matches_snapshot(request: pytest.FixtureRequest) -> None:
    report_data = _serialized_report()
    if request.config.getoption("--snapshot-update", default=False):
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(json.dumps(report_data, indent=2, sort_keys=True))
        pytest.skip("snapshot updated")
    if not SNAPSHOT_PATH.exists():
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(json.dumps(report_data, indent=2, sort_keys=True))
        pytest.skip("snapshot created on first run")
    expected = json.loads(SNAPSHOT_PATH.read_text())
    assert report_data == expected, (
        "Report changed. If intentional, run `pytest --snapshot-update`."
    )


def test_pipeline_smoke_no_workouts() -> None:
    f = parse_frames(
        load_zip(fixtures_dir() / "no_workouts.zip", max_bytes=50 * 1024 * 1024)
    )
    report = build_report(f)
    assert report.workouts is None
    assert report.dials.recovery.value > 0


def test_pipeline_smoke_no_journal() -> None:
    f = parse_frames(
        load_zip(fixtures_dir() / "no_journal.zip", max_bytes=50 * 1024 * 1024)
    )
    report = build_report(f)
    assert report.journal is None
```

- [ ] **Step 3: Add the `--snapshot-update` CLI flag to pytest**

Append to `apps/api/tests/conftest.py` (create the file if it doesn't exist; otherwise add the function below):

```python
import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--snapshot-update",
        action="store_true",
        default=False,
        help="Regenerate snapshot files instead of asserting against them.",
    )
```

- [ ] **Step 4: Generate the snapshot on first run**

```bash
uv run pytest tests/analysis/test_pipeline.py -v
```

Expected first run: `1 skipped` (snapshot created) + `2 passed`. Run again:

```bash
uv run pytest tests/analysis/test_pipeline.py -v
```

Expected: `3 passed`.

- [ ] **Step 5: Inspect the snapshot file**

```bash
ls -la apps/api/tests/snapshots/happy_report.json
head -40 apps/api/tests/snapshots/happy_report.json
```

Expected: a non-empty JSON file containing the canonical report.

- [ ] **Step 6: Run the full test suite**

```bash
uv run pytest -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add apps/api/
git commit -m "feat(api): add pipeline orchestrator and snapshot test

- build_report() composes period/dials/metrics/recovery/sleep/strain/workouts/journal/trends/insights
- Snapshot test locks in canonical happy_report.json (use --snapshot-update to regenerate)
- Smoke tests for no-workouts and no-journal fixtures"
```

---

## Task 16: Database (SQLAlchemy + Alembic)

**Files:**
- Modify: `apps/api/pyproject.toml` (add sqlalchemy, asyncpg, alembic, freezegun)
- Create: `apps/api/app/db/__init__.py`
- Create: `apps/api/app/db/base.py`
- Create: `apps/api/app/db/session.py`
- Create: `apps/api/app/db/models.py`
- Create: `apps/api/alembic.ini`
- Create: `apps/api/alembic/env.py`
- Create: `apps/api/alembic/script.py.mako`
- Create: `apps/api/alembic/versions/0001_create_shared_reports.py`
- Modify: `apps/api/tests/conftest.py`
- Create: `apps/api/tests/db/__init__.py`
- Create: `apps/api/tests/db/test_shared_report.py`

- [ ] **Step 1: Add deps**

```bash
cd ~/projects/whoop-lens/apps/api
uv add "sqlalchemy[asyncio]>=2.0" "asyncpg>=0.29" "alembic>=1.13" "nanoid>=2.0"
uv add --dev "freezegun>=1.5"
```

- [ ] **Step 2: Implement `db/base.py`**

Create `apps/api/app/db/__init__.py` (empty file).

Create `apps/api/app/db/base.py`:

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 3: Implement `db/session.py`**

Create `apps/api/app/db/session.py`:

```python
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.settings import get_settings

_settings = get_settings()
engine = create_async_engine(_settings.database_url, future=True, pool_pre_ping=True)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session
```

- [ ] **Step 4: Implement `db/models.py`**

Create `apps/api/app/db/models.py`:

```python
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SharedReport(Base):
    __tablename__ = "shared_reports"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    report: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (Index("idx_shared_reports_expires", "expires_at"),)
```

- [ ] **Step 5: Initialize Alembic**

```bash
cd ~/projects/whoop-lens/apps/api
uv run alembic init -t async alembic
```

This creates `alembic.ini` and `alembic/env.py`. Edit `apps/api/alembic.ini` and find the line `sqlalchemy.url = ...` — leave it commented (we set it from env in env.py).

Edit `apps/api/alembic/env.py` — replace the entire file with:

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.db.base import Base
from app.db.models import SharedReport  # noqa: F401  needed for autogenerate
from app.settings import get_settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

config.set_main_option("sqlalchemy.url", get_settings().database_url)


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

- [ ] **Step 6: Generate the migration**

Make sure `DATABASE_URL` is set in your shell, then:

```bash
uv run alembic revision --autogenerate -m "create shared_reports table"
```

Find the new file under `apps/api/alembic/versions/<hash>_create_shared_reports_table.py`. **Rename it** to `0001_create_shared_reports.py` (so order is stable). Open it and confirm it creates `shared_reports` with `id`, `report`, `created_at`, `expires_at` columns plus the index. If the autogenerated file is messy, replace it with:

```python
"""create shared_reports table

Revision ID: 0001
Revises:
Create Date: 2026-04-07 00:00:00.000000
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "shared_reports",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("report", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_shared_reports_expires", "shared_reports", ["expires_at"])


def downgrade() -> None:
    op.drop_index("idx_shared_reports_expires", table_name="shared_reports")
    op.drop_table("shared_reports")
```

- [ ] **Step 7: Apply the migration**

```bash
uv run alembic upgrade head
```

Expected: `INFO  [alembic.runtime.migration] Running upgrade  -> 0001, create shared_reports table`.

- [ ] **Step 8: Set up the test session fixture**

Replace `apps/api/tests/conftest.py` with:

```python
import asyncio
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, async_sessionmaker

from app.db.base import Base
from app.db.session import engine


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--snapshot-update",
        action="store_true",
        default=False,
        help="Regenerate snapshot files instead of asserting against them.",
    )


@pytest_asyncio.fixture(scope="session")
async def _create_schema() -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(_create_schema: None) -> AsyncIterator[AsyncSession]:
    """Per-test session that rolls back at the end."""
    connection: AsyncConnection = await engine.connect()
    trans = await connection.begin()
    factory = async_sessionmaker(bind=connection, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session
    await trans.rollback()
    await connection.close()
```

- [ ] **Step 9: Write the SharedReport ORM smoke test**

Create `apps/api/tests/db/__init__.py` (empty).

Create `apps/api/tests/db/test_shared_report.py`:

```python
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SharedReport


@pytest.mark.asyncio
async def test_insert_and_select_shared_report(db_session: AsyncSession) -> None:
    report = {"hello": "world"}
    expires = datetime.now(timezone.utc) + timedelta(days=30)
    db_session.add(SharedReport(id="abc12345", report=report, expires_at=expires))
    await db_session.flush()

    result = await db_session.execute(
        select(SharedReport).where(SharedReport.id == "abc12345")
    )
    row = result.scalar_one()
    assert row.report == {"hello": "world"}
    assert row.expires_at == expires
```

- [ ] **Step 10: Run DB tests**

```bash
uv run pytest tests/db/ -v
```

Expected: `1 passed`.

- [ ] **Step 11: Commit**

```bash
git add apps/api/
git commit -m "feat(api): add SQLAlchemy 2.0 async + Alembic + SharedReport model

- Base, async engine, session factory, get_session FastAPI dep
- SharedReport ORM with id PK, JSONB report, expires_at index
- Alembic configured to use DATABASE_URL from settings
- Migration 0001 creates shared_reports
- Per-test rollback session fixture in conftest.py
- Smoke test passing"
```

---

## Task 17: POST /share endpoint

**Files:**
- Create: `apps/api/app/routers/__init__.py`
- Create: `apps/api/app/routers/share.py`
- Create: `apps/api/tests/routers/__init__.py`
- Create: `apps/api/tests/routers/test_share.py`
- Modify: `apps/api/app/main.py`

- [ ] **Step 1: Write the share endpoint test**

Create `apps/api/tests/routers/__init__.py` (empty).

Create `apps/api/tests/routers/test_share.py`:

```python
import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.fixtures.build_fixtures import build_all_fixtures, fixtures_dir


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures() -> None:
    build_all_fixtures()


def _sample_report_dict() -> dict:
    from app.analysis.pipeline import build_report
    from app.parsing.frames import parse_frames
    from app.parsing.zip_loader import load_zip
    f = parse_frames(load_zip(fixtures_dir() / "happy.zip", max_bytes=50 * 1024 * 1024))
    return json.loads(build_report(f).model_dump_json(by_alias=True))


@pytest.mark.asyncio
async def test_share_creates_row_and_returns_id(_create_schema: None) -> None:
    payload = {"report": _sample_report_dict()}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/share", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["url"].startswith("/r/")
    assert "expires_at" in data


@pytest.mark.asyncio
async def test_share_rejects_invalid_report(_create_schema: None) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/share", json={"report": {"schema_version": 1}})
    assert resp.status_code == 422
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/routers/test_share.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.routers'` or similar.

- [ ] **Step 3: Implement `routers/__init__.py` and `share.py`**

Create `apps/api/app/routers/__init__.py` (empty).

Create `apps/api/app/routers/share.py`:

```python
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from nanoid import generate as nanoid_generate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SharedReport
from app.db.session import get_session
from app.models.report import WhoopReport
from app.models.share import ShareCreateRequest, ShareCreateResponse
from app.settings import get_settings

router = APIRouter()
settings = get_settings()


@router.post(
    "/share", response_model=ShareCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_share(
    req: ShareCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> ShareCreateResponse:
    short_id = nanoid_generate(size=8)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.share_ttl_days)
    row = SharedReport(
        id=short_id,
        report=req.report.model_dump(mode="json", by_alias=True),
        expires_at=expires_at,
    )
    session.add(row)
    await session.commit()
    return ShareCreateResponse(id=short_id, url=f"/r/{short_id}", expires_at=expires_at)


@router.get("/r/{share_id}", response_model=WhoopReport)
async def get_shared_report(
    share_id: str,
    session: AsyncSession = Depends(get_session),
) -> WhoopReport:
    row = (
        await session.execute(
            select(SharedReport).where(SharedReport.id == share_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    if row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=404, detail="expired")
    return WhoopReport.model_validate(row.report)
```

- [ ] **Step 4: Wire the router into `main.py`**

Replace `apps/api/app/main.py`:

```python
from fastapi import FastAPI

from app.logging_config import configure_logging, get_logger
from app.routers import share
from app.settings import get_settings

settings = get_settings()
configure_logging(level=settings.log_level)
log = get_logger(__name__)

app = FastAPI(title="Whoop Lens API", version="0.1.0")
app.include_router(share.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "whoop-lens-api", "version": "0.1.0"}
```

- [ ] **Step 5: Run share tests**

```bash
uv run pytest tests/routers/test_share.py -v
```

Expected: `2 passed`.

- [ ] **Step 6: Add a GET /r/{id} test**

Append to `apps/api/tests/routers/test_share.py`:

```python
@pytest.mark.asyncio
async def test_get_shared_report_round_trip(_create_schema: None) -> None:
    payload = {"report": _sample_report_dict()}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post("/share", json=payload)
        share_id = create_resp.json()["id"]
        get_resp = await client.get(f"/r/{share_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["schema_version"] == 1


@pytest.mark.asyncio
async def test_get_shared_report_404(_create_schema: None) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/r/doesnotexist")
    assert resp.status_code == 404
```

Run again:

```bash
uv run pytest tests/routers/test_share.py -v
```

Expected: `4 passed`.

- [ ] **Step 7: Commit**

```bash
git add apps/api/
git commit -m "feat(api): add POST /share and GET /r/{id} endpoints

- nanoid 8-char IDs, JSONB report storage, 30-day TTL from settings
- 422 on invalid report shape (Pydantic validation)
- 404 on not-found and on expired
- 4 router tests passing"
```

---

## Task 18: POST /analyze endpoint

**Files:**
- Create: `apps/api/app/routers/analyze.py`
- Create: `apps/api/tests/routers/test_analyze.py`
- Modify: `apps/api/app/main.py`

- [ ] **Step 1: Write the analyze endpoint test**

Create `apps/api/tests/routers/test_analyze.py`:

```python
import io

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.fixtures.build_fixtures import build_all_fixtures, fixtures_dir


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures() -> None:
    build_all_fixtures()


@pytest.mark.asyncio
async def test_analyze_happy() -> None:
    zip_bytes = (fixtures_dir() / "happy.zip").read_bytes()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/analyze",
            files={"file": ("my_whoop_data.zip", zip_bytes, "application/zip")},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["schema_version"] == 1
    assert data["dials"]["recovery"]["unit"] == "%"


@pytest.mark.asyncio
async def test_analyze_corrupt_zip() -> None:
    zip_bytes = (fixtures_dir() / "corrupt.zip").read_bytes()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/analyze",
            files={"file": ("bad.zip", zip_bytes, "application/zip")},
        )
    assert resp.status_code == 400
    assert resp.json()["code"] in ("not_a_zip", "corrupt_zip")


@pytest.mark.asyncio
async def test_analyze_wrong_format() -> None:
    zip_bytes = (fixtures_dir() / "wrong_format.zip").read_bytes()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/analyze",
            files={"file": ("wrong.zip", zip_bytes, "application/zip")},
        )
    assert resp.status_code == 400
    assert resp.json()["code"] == "unexpected_schema"


@pytest.mark.asyncio
async def test_analyze_no_workouts_succeeds() -> None:
    zip_bytes = (fixtures_dir() / "no_workouts.zip").read_bytes()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/analyze",
            files={"file": ("nw.zip", zip_bytes, "application/zip")},
        )
    assert resp.status_code == 200
    assert resp.json()["workouts"] is None


@pytest.mark.asyncio
async def test_analyze_oversize() -> None:
    big = b"\x00" * (51 * 1024 * 1024)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/analyze",
            files={"file": ("big.zip", big, "application/zip")},
        )
    assert resp.status_code == 413
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/routers/test_analyze.py -v
```

Expected: failures because the route doesn't exist yet.

- [ ] **Step 3: Implement `routers/analyze.py`**

Create `apps/api/app/routers/analyze.py`:

```python
import uuid
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.analysis.pipeline import build_report
from app.logging_config import get_logger
from app.parsing.errors import (
    CorruptZipError,
    FileTooLargeError,
    MissingRequiredFileError,
    NoDataError,
    NotAZipError,
    ParseError,
    UnexpectedSchemaError,
)
from app.parsing.frames import parse_frames
from app.parsing.zip_loader import load_zip
from app.settings import get_settings

router = APIRouter()
settings = get_settings()
log = get_logger(__name__)


@router.post("/analyze")
async def analyze(file: Annotated[UploadFile, File()]) -> JSONResponse:
    max_bytes = settings.max_upload_mb * 1024 * 1024

    # Stream into memory but enforce the cap
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"code": "file_too_large", "limit_mb": settings.max_upload_mb},
            )
        chunks.append(chunk)
    body = b"".join(chunks)

    import io

    try:
        loaded = load_zip(io.BytesIO(body), max_bytes=max_bytes)
        frames = parse_frames(loaded)
        report = build_report(frames)
    except FileTooLargeError as e:
        return JSONResponse(
            status_code=413,
            content={"code": e.code, "limit_mb": e.limit_mb},
        )
    except NotAZipError as e:
        return JSONResponse(status_code=400, content={"code": e.code})
    except CorruptZipError as e:
        return JSONResponse(status_code=400, content={"code": e.code})
    except MissingRequiredFileError as e:
        return JSONResponse(
            status_code=400, content={"code": e.code, "file": e.file}
        )
    except UnexpectedSchemaError as e:
        return JSONResponse(
            status_code=400,
            content={
                "code": e.code,
                "file": e.file,
                "missing_cols": e.missing,
                "extra_cols": e.extra,
            },
        )
    except NoDataError as e:
        return JSONResponse(
            status_code=400, content={"code": e.code, "file": e.file}
        )
    except ParseError as e:
        return JSONResponse(status_code=400, content={"code": e.code})
    except Exception:
        error_id = uuid.uuid4().hex
        log.exception("analysis_failed", error_id=error_id)
        return JSONResponse(
            status_code=500,
            content={"code": "analysis_failed", "error_id": error_id},
        )

    return JSONResponse(
        status_code=200, content=report.model_dump(mode="json", by_alias=True)
    )
```

- [ ] **Step 4: Wire the analyze router**

Modify `apps/api/app/main.py` — add `analyze` import and `include_router` line:

```python
from fastapi import FastAPI

from app.logging_config import configure_logging, get_logger
from app.routers import analyze, share
from app.settings import get_settings

settings = get_settings()
configure_logging(level=settings.log_level)
log = get_logger(__name__)

app = FastAPI(title="Whoop Lens API", version="0.1.0")
app.include_router(analyze.router)
app.include_router(share.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "whoop-lens-api", "version": "0.1.0"}
```

- [ ] **Step 5: Run analyze tests**

```bash
uv run pytest tests/routers/test_analyze.py -v
```

Expected: `5 passed`.

- [ ] **Step 6: Commit**

```bash
git add apps/api/
git commit -m "feat(api): add POST /analyze endpoint with full error mapping

- Streams upload, enforces MAX_UPLOAD_MB cap
- Maps each ParseError subclass to the correct 400/413 + code
- Catches unhandled exceptions, logs with error_id, returns 500
- 5 endpoint tests covering happy + each error path"
```

---

## Task 19: Healthcheck, CORS, lifespan, cleanup

**Files:**
- Create: `apps/api/app/routers/health.py`
- Create: `apps/api/app/db/cleanup.py`
- Modify: `apps/api/app/main.py`
- Create: `apps/api/tests/routers/test_health.py`
- Create: `apps/api/tests/db/test_cleanup.py`

- [ ] **Step 1: Write the health test**

Create `apps/api/tests/routers/test_health.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_healthz_ok(_create_schema: None) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["db"] == "ok"
```

- [ ] **Step 2: Implement `routers/health.py`**

Create `apps/api/app/routers/health.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session

router = APIRouter()


@router.get("/healthz")
async def healthz(session: AsyncSession = Depends(get_session)) -> dict[str, object]:
    try:
        await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:  # noqa: BLE001
        db_status = "down"
    return {"ok": db_status == "ok", "db": db_status}
```

- [ ] **Step 3: Implement `db/cleanup.py`**

Create `apps/api/app/db/cleanup.py`:

```python
import asyncio
from datetime import datetime, timezone

from sqlalchemy import delete

from app.db.models import SharedReport
from app.db.session import SessionFactory
from app.logging_config import get_logger

log = get_logger(__name__)
CLEANUP_INTERVAL_SECONDS = 6 * 60 * 60


async def delete_expired_now() -> int:
    """Run a single delete pass. Returns rows deleted. Useful in tests."""
    async with SessionFactory() as session:
        result = await session.execute(
            delete(SharedReport).where(SharedReport.expires_at < datetime.now(timezone.utc))
        )
        await session.commit()
        return int(result.rowcount or 0)


async def periodic_cleanup() -> None:
    while True:
        try:
            n = await delete_expired_now()
            log.info("cleanup_ran", deleted=n)
        except Exception:  # noqa: BLE001
            log.exception("cleanup_failed")
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
```

- [ ] **Step 4: Add lifespan + CORS to main.py**

Replace `apps/api/app/main.py`:

```python
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.cleanup import periodic_cleanup
from app.logging_config import configure_logging, get_logger
from app.routers import analyze, health, share
from app.settings import get_settings

settings = get_settings()
configure_logging(level=settings.log_level)
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    cleanup_task = asyncio.create_task(periodic_cleanup())
    log.info("lifespan_started")
    try:
        yield
    finally:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        log.info("lifespan_stopped")


app = FastAPI(title="Whoop Lens API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(share.router)
app.include_router(health.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "whoop-lens-api", "version": "0.1.0"}
```

- [ ] **Step 5: Write the cleanup test**

Create `apps/api/tests/db/test_cleanup.py`:

```python
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.cleanup import delete_expired_now
from app.db.models import SharedReport


@pytest.mark.asyncio
async def test_cleanup_removes_only_expired(db_session: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    db_session.add(
        SharedReport(id="alive001", report={"x": 1}, expires_at=now + timedelta(days=1))
    )
    db_session.add(
        SharedReport(id="dead0001", report={"x": 1}, expires_at=now - timedelta(days=1))
    )
    await db_session.flush()
    await db_session.commit()

    deleted = await delete_expired_now()
    assert deleted >= 1

    rows = (await db_session.execute(select(SharedReport))).scalars().all()
    ids = {r.id for r in rows}
    assert "alive001" in ids
    assert "dead0001" not in ids
```

- [ ] **Step 6: Run new tests**

```bash
uv run pytest tests/routers/test_health.py tests/db/test_cleanup.py -v
```

Expected: `2 passed`.

- [ ] **Step 7: Commit**

```bash
git add apps/api/
git commit -m "feat(api): add /healthz, CORS, lifespan, periodic cleanup

- /healthz pings DB and returns ok status
- CORS middleware reads cors_origin from settings
- lifespan starts/stops periodic_cleanup background task
- delete_expired_now() is reusable + tested
- 2 new tests passing"
```

---

## Task 20: Final lint, type-check, full suite

**Files:**
- Modify: `apps/api/pyproject.toml` (if needed)

- [ ] **Step 1: Run ruff**

```bash
cd ~/projects/whoop-lens/apps/api
uv run ruff check
```

Expected: no errors. Fix anything that comes up. Common fixes: unused imports, sorted imports.

- [ ] **Step 2: Run pyright**

```bash
uv run pyright
```

Expected: no errors. If pandas types complain, you can narrow `Series` returns explicitly with `# type: ignore[arg-type]` on the offending line — these are well-known limitations.

- [ ] **Step 3: Run the full pytest suite**

```bash
uv run pytest -v
```

Expected: all green.

- [ ] **Step 4: Commit any lint fixes**

```bash
git add apps/api/
git diff --cached --quiet || git commit -m "chore(api): lint and type-check fixes"
```

---

## Task 21: Railway deploy config

**Files:**
- Create: `apps/api/railway.toml`
- Modify: `apps/api/README.md`

- [ ] **Step 1: Create `railway.toml`**

Create `apps/api/railway.toml`:

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2"
healthcheckPath = "/healthz"
healthcheckTimeout = 30
restartPolicyType = "always"
```

- [ ] **Step 2: Append deploy notes to README**

Append to `apps/api/README.md`:

```markdown

## Deploy (Railway)

1. Connect this repo to Railway
2. Set Root Directory = `apps/api`
3. Add a Postgres add-on (sets `DATABASE_URL` automatically)
4. Set env vars:
   - `CORS_ORIGIN=https://whooplens.app`
   - `SHARE_TTL_DAYS=30`
   - `MAX_UPLOAD_MB=50`
   - `LOG_LEVEL=INFO`
5. Deploy. Health is at `/healthz`.

## Env vars

| Key | Default | Notes |
|---|---|---|
| `DATABASE_URL` | — | Required. Set by Railway Postgres add-on. |
| `CORS_ORIGIN` | `http://localhost:3000` | Comma-separated origins |
| `MAX_UPLOAD_MB` | 50 | |
| `SHARE_TTL_DAYS` | 30 | |
| `LOG_LEVEL` | INFO | |
```

- [ ] **Step 3: Commit**

```bash
git add apps/api/
git commit -m "chore(api): add railway.toml and deploy README"
```

---

## Task 22: GitHub Actions CI (api job)

**Files:**
- Create: `.github/workflows/ci.yml` (at repo root)

- [ ] **Step 1: Create the workflow**

Create `~/projects/whoop-lens/.github/workflows/ci.yml`:

```yaml
name: ci
on:
  push:
    branches: [main]
  pull_request:

jobs:
  api:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_USER: postgres
          POSTGRES_DB: postgres
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    defaults:
      run:
        working-directory: apps/api
    env:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/postgres
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with:
          version: "0.10.4"
      - run: uv python install 3.13.12
      - run: uv sync
      - run: uv run ruff check
      - run: uv run pyright
      - run: uv run alembic upgrade head
      - run: uv run pytest -v
```

- [ ] **Step 2: Push and observe**

```bash
cd ~/projects/whoop-lens
git add .github/
git commit -m "ci: add api job with Postgres service"
git push  # only if you have a remote configured
```

If you don't have a remote yet, that's fine — the workflow file is committed and will run on the first push. Verify locally first:

```bash
cd ~/projects/whoop-lens/apps/api
uv run ruff check && uv run pyright && uv run pytest -q
```

Expected: all green.

---

## Final verification checklist

After Task 22, run this end-to-end smoke from the repo root:

```bash
cd ~/projects/whoop-lens/apps/api
uv run alembic upgrade head
uv run pytest -q
uv run uvicorn app.main:app --port 8001 &
sleep 2
curl -s http://localhost:8001/healthz
curl -s -F "file=@tests/fixtures/zips/happy.zip" http://localhost:8001/analyze | head -c 400
kill %1
```

Expected:
- All tests pass
- `{"ok":true,"db":"ok"}` from /healthz
- A JSON object starting with `{"schema_version":1,"period":...` from /analyze

---

## Self-review notes

**Spec coverage:**
- §1 product summary → not part of code, satisfied by repo structure
- §2 architecture → Tasks 1, 16, 17, 18, 21 establish the shape
- §3 backend modules → every file in §3 has a creation task
- §4 frontend → out of scope for this plan
- §5 type contract → Task 3 mirrors the spec types
- §6 error handling → Task 4 (errors), Task 18 (mapping)
- §7 testing → every code task has a TDD pair; snapshot in Task 15
- §8 deployment → Task 21
- §9 conventions → followed in commits
- §10 visual → frontend concern
- §11 insight rules → Tasks 12-14
- §12 implementation notes → addressed (parser handles missing/empty optional files)

**Placeholder scan:** none. Every code block is concrete.

**Type consistency:** `WhoopReport`, `Insight`, `ParsedFrames`, and the routing types use the same names across tasks.

**Frontend plan:** to be written as `2026-04-07-whoop-lens-frontend.md` after this plan ships and the API is running.
