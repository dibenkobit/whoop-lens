"""Parse loaded CSV bytes into typed pandas DataFrames.

We always read as strings first, validate columns, then explicitly coerce
each column with the right dtype. Rows with NaT timestamps are dropped;
rows with all-NaN are dropped; everything else is left for the analysis
layer to handle.
"""
import io
from dataclasses import dataclass

import pandas as pd  # pyright: ignore[reportMissingTypeStubs]

from app.parsing.csv_schema import (
    JOURNAL_REQUIRED_COLUMNS,
    WORKOUTS_REQUIRED_COLUMNS,
    CsvFile,
    validate_columns,
)
from app.parsing.errors import NoDataError
from app.parsing.zip_loader import LoadedZip

# Columns that should be parsed as datetimes (where present)
DATETIME_COLUMNS: set[str] = {
    "Cycle start time",
    "Cycle end time",
    "Sleep onset",
    "Wake onset",
    "Workout start time",
    "Workout end time",
}

# Columns that should be parsed as floats (where present)
FLOAT_COLUMNS: set[str] = {
    "Recovery score %",
    "Resting heart rate (bpm)",
    "Heart rate variability (ms)",
    "Skin temp (celsius)",
    "Blood oxygen %",
    "Day Strain",
    "Energy burned (cal)",
    "Max HR (bpm)",
    "Average HR (bpm)",
    "Sleep performance %",
    "Respiratory rate (rpm)",
    "Asleep duration (min)",
    "In bed duration (min)",
    "Light sleep duration (min)",
    "Deep (SWS) duration (min)",
    "REM duration (min)",
    "Awake duration (min)",
    "Sleep need (min)",
    "Sleep debt (min)",
    "Sleep efficiency %",
    "Sleep consistency %",
    "Duration (min)",
    "Activity Strain",
    "HR Zone 1 %",
    "HR Zone 2 %",
    "HR Zone 3 %",
    "HR Zone 4 %",
    "HR Zone 5 %",
}


@dataclass(frozen=True)
class ParsedFrames:
    cycles: pd.DataFrame
    sleeps: pd.DataFrame
    workouts: pd.DataFrame
    journal: pd.DataFrame


def _read_csv_strict(content: bytes, file: CsvFile) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False, na_values=[""])
    validate_columns(file, df.columns.tolist())  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
    return df


def _coerce_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:  # pyright: ignore[reportUnknownVariableType]
        if col in DATETIME_COLUMNS:
            df[col] = pd.to_datetime(df[col], errors="coerce")  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        elif col in FLOAT_COLUMNS:
            numeric = pd.to_numeric(df[col], errors="coerce")  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportUnknownVariableType]
            df[col] = numeric.astype("float64")  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
    return df


def parse_frames(loaded: LoadedZip) -> ParsedFrames:
    cycles_raw = _read_csv_strict(loaded.files[CsvFile.CYCLES], CsvFile.CYCLES)
    sleeps_raw = _read_csv_strict(loaded.files[CsvFile.SLEEPS], CsvFile.SLEEPS)

    cycles = _coerce_columns(cycles_raw)
    cycles = cycles.dropna(subset=["Cycle start time"])
    if cycles.empty:
        raise NoDataError(CsvFile.CYCLES.value)

    sleeps = _coerce_columns(sleeps_raw)
    sleeps = sleeps.dropna(subset=["Cycle start time"])

    workouts_bytes = loaded.files.get(CsvFile.WORKOUTS, b"")
    if workouts_bytes:
        workouts_raw = _read_csv_strict(workouts_bytes, CsvFile.WORKOUTS)
        workouts = _coerce_columns(workouts_raw)
        workouts = workouts.dropna(subset=["Workout start time"])
    else:
        workouts = pd.DataFrame(columns=list(WORKOUTS_REQUIRED_COLUMNS))

    journal_bytes = loaded.files.get(CsvFile.JOURNAL, b"")
    if journal_bytes:
        journal_raw = _read_csv_strict(journal_bytes, CsvFile.JOURNAL)
        journal = _coerce_columns(journal_raw)
    else:
        journal = pd.DataFrame(columns=list(JOURNAL_REQUIRED_COLUMNS))

    return ParsedFrames(
        cycles=cycles.reset_index(drop=True),
        sleeps=sleeps.reset_index(drop=True),
        workouts=workouts.reset_index(drop=True),
        journal=journal.reset_index(drop=True),
    )
