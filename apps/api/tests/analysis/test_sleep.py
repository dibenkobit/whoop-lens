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
