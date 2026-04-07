import zipfile
from pathlib import Path

import pytest

from tests.fixtures.build_fixtures import (
    HAPPY_DAYS,
    fixtures_dir,
)


def test_happy_zip_exists_and_has_4_files() -> None:
    p = fixtures_dir() / "happy.zip"
    assert p.exists()
    with zipfile.ZipFile(p) as zf:
        names = sorted(zf.namelist())
    assert names == sorted(
        [
            "physiological_cycles.csv",
            "sleeps.csv",
            "workouts.csv",
            "journal_entries.csv",
        ]
    )


def test_happy_cycles_has_correct_row_count() -> None:
    import csv
    p = fixtures_dir() / "happy.zip"
    with zipfile.ZipFile(p) as zf, zf.open("physiological_cycles.csv") as f:
        reader = csv.reader(line.decode("utf-8") for line in f.readlines())
        rows = list(reader)
    # header + HAPPY_DAYS rows
    assert len(rows) == HAPPY_DAYS + 1


def test_minimal_zip_has_14_days() -> None:
    import csv
    p = fixtures_dir() / "minimal_14d.zip"
    with zipfile.ZipFile(p) as zf, zf.open("physiological_cycles.csv") as f:
        rows = list(csv.reader(line.decode("utf-8") for line in f.readlines()))
    assert len(rows) == 15  # 14 + header


def test_no_workouts_zip_has_empty_workouts() -> None:
    import csv
    p = fixtures_dir() / "no_workouts.zip"
    with zipfile.ZipFile(p) as zf, zf.open("workouts.csv") as f:
        rows = list(csv.reader(line.decode("utf-8") for line in f.readlines()))
    assert len(rows) == 1  # only header


def test_corrupt_zip_is_invalid() -> None:
    p = fixtures_dir() / "corrupt.zip"
    with pytest.raises(zipfile.BadZipFile):
        zipfile.ZipFile(p)


def test_wrong_format_zip_has_renamed_column() -> None:
    p = fixtures_dir() / "wrong_format.zip"
    with zipfile.ZipFile(p) as zf, zf.open("physiological_cycles.csv") as f:
        header = f.readline().decode("utf-8").strip()
    assert "Recovery score %" not in header
    assert "Recovery_score" in header
