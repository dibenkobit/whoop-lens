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
