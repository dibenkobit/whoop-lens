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


def test_validate_columns_extras_populated_when_required_missing() -> None:
    cols = [c for c in CYCLES_REQUIRED_COLUMNS if c != "Recovery score %"]
    cols += ["zzz_phantom", "aaa_phantom"]
    with pytest.raises(UnexpectedSchemaError) as exc:
        validate_columns(CsvFile.CYCLES, cols)
    assert exc.value.extra == ["aaa_phantom", "zzz_phantom"]
    assert exc.value.missing == ["Recovery score %"]


def test_validate_columns_missing_list_is_sorted() -> None:
    cols = [
        c
        for c in CYCLES_REQUIRED_COLUMNS
        if c not in {"Recovery score %", "Day Strain", "Sleep onset"}
    ]
    with pytest.raises(UnexpectedSchemaError) as exc:
        validate_columns(CsvFile.CYCLES, cols)
    assert exc.value.missing == sorted(exc.value.missing)
    assert set(exc.value.missing) == {"Day Strain", "Recovery score %", "Sleep onset"}
