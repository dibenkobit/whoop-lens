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
    from datetime import datetime, timedelta
    f = _happy_frames()
    base = datetime(2025, 1, 1, 2, 30, 0)
    onsets = pd.to_datetime([base + timedelta(days=d) for d in range(len(f.cycles))])
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
