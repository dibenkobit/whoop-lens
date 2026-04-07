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


def _serialized_report() -> dict:  # type: ignore[type-arg]
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
