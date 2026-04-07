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


def test_insight_overtraining_triggers() -> None:
    f = _happy_frames()
    # Rows 0-4: high strain, next-day recovery is low (rows 1-5 = 25%)
    # Rows 6+: no high strain, high recovery (80%) → baseline is dominated by high values
    f.cycles.loc[:, "Recovery score %"] = 80.0
    f.cycles.loc[:, "Day Strain"] = 8.0
    f.cycles.loc[:5, "Day Strain"] = 16.0   # high-strain days
    f.cycles.loc[1:6, "Recovery score %"] = 25.0  # next-day recovery after strain
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
