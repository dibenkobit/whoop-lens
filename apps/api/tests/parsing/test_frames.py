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
        JOURNAL_REQUIRED_COLUMNS,
        SLEEPS_REQUIRED_COLUMNS,
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
