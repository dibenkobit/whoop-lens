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
