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
