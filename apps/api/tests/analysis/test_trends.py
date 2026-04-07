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
