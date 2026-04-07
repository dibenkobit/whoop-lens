"""Source of truth for the column shapes we expect in the Whoop export.

Column lists are taken from a real Whoop export (April 2026 format). If Whoop
changes the export, only this file should need to update.
"""
from enum import Enum

from app.parsing.errors import UnexpectedSchemaError


class CsvFile(str, Enum):
    CYCLES = "physiological_cycles.csv"
    SLEEPS = "sleeps.csv"
    WORKOUTS = "workouts.csv"
    JOURNAL = "journal_entries.csv"


CYCLES_REQUIRED_COLUMNS: tuple[str, ...] = (
    "Cycle start time",
    "Cycle end time",
    "Cycle timezone",
    "Recovery score %",
    "Resting heart rate (bpm)",
    "Heart rate variability (ms)",
    "Skin temp (celsius)",
    "Blood oxygen %",
    "Day Strain",
    "Energy burned (cal)",
    "Max HR (bpm)",
    "Average HR (bpm)",
    "Sleep onset",
    "Wake onset",
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
)

SLEEPS_REQUIRED_COLUMNS: tuple[str, ...] = (
    "Cycle start time",
    "Cycle end time",
    "Cycle timezone",
    "Sleep onset",
    "Wake onset",
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
    "Nap",
)

WORKOUTS_REQUIRED_COLUMNS: tuple[str, ...] = (
    "Cycle start time",
    "Cycle end time",
    "Cycle timezone",
    "Workout start time",
    "Workout end time",
    "Duration (min)",
    "Activity name",
    "Activity Strain",
    "Energy burned (cal)",
    "Max HR (bpm)",
    "Average HR (bpm)",
    "HR Zone 1 %",
    "HR Zone 2 %",
    "HR Zone 3 %",
    "HR Zone 4 %",
    "HR Zone 5 %",
    "GPS enabled",
)

JOURNAL_REQUIRED_COLUMNS: tuple[str, ...] = (
    "Cycle start time",
    "Cycle end time",
    "Cycle timezone",
    "Question text",
    "Answered yes",
    "Notes",
)


_REQUIRED: dict[CsvFile, tuple[str, ...]] = {
    CsvFile.CYCLES: CYCLES_REQUIRED_COLUMNS,
    CsvFile.SLEEPS: SLEEPS_REQUIRED_COLUMNS,
    CsvFile.WORKOUTS: WORKOUTS_REQUIRED_COLUMNS,
    CsvFile.JOURNAL: JOURNAL_REQUIRED_COLUMNS,
}


def validate_columns(file: CsvFile, actual: list[str]) -> None:
    required = set(_REQUIRED[file])
    actual_set = set(actual)
    missing = sorted(required - actual_set)
    if missing:
        extra = sorted(actual_set - required)
        raise UnexpectedSchemaError(file=file.value, missing=missing, extra=extra)
