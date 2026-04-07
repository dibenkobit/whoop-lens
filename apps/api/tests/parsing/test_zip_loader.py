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
