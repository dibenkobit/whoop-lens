import pytest

from app.parsing.csv_schema import (
    CYCLES_REQUIRED_COLUMNS,
    JOURNAL_REQUIRED_COLUMNS,
    SLEEPS_REQUIRED_COLUMNS,
    WORKOUTS_REQUIRED_COLUMNS,
    CsvFile,
    validate_columns,
)
from app.parsing.errors import UnexpectedSchemaError


def test_cycles_columns_listed() -> None:
    assert "Recovery score %" in CYCLES_REQUIRED_COLUMNS
    assert "Heart rate variability (ms)" in CYCLES_REQUIRED_COLUMNS
    assert "Sleep onset" in CYCLES_REQUIRED_COLUMNS


def test_validate_columns_happy() -> None:
    extra = ["A useless extra column"]
    validate_columns(
        CsvFile.CYCLES,
        list(CYCLES_REQUIRED_COLUMNS) + extra,
    )


def test_validate_columns_missing_required() -> None:
    cols = [c for c in CYCLES_REQUIRED_COLUMNS if c != "Recovery score %"]
    with pytest.raises(UnexpectedSchemaError) as exc:
        validate_columns(CsvFile.CYCLES, cols)
    assert "Recovery score %" in exc.value.missing
    assert exc.value.file == "physiological_cycles.csv"


def test_validate_columns_for_each_file() -> None:
    validate_columns(CsvFile.CYCLES, list(CYCLES_REQUIRED_COLUMNS))
    validate_columns(CsvFile.SLEEPS, list(SLEEPS_REQUIRED_COLUMNS))
    validate_columns(CsvFile.WORKOUTS, list(WORKOUTS_REQUIRED_COLUMNS))
    validate_columns(CsvFile.JOURNAL, list(JOURNAL_REQUIRED_COLUMNS))
