"""Generate deterministic fixture zips for the parser and pipeline tests.

Uses a seeded numpy RNG so the snapshot tests are stable across machines.
"""
import csv
import io
import random
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

from app.parsing.csv_schema import (
    CYCLES_REQUIRED_COLUMNS,
    JOURNAL_REQUIRED_COLUMNS,
    SLEEPS_REQUIRED_COLUMNS,
    WORKOUTS_REQUIRED_COLUMNS,
)

HAPPY_DAYS = 60
MINIMAL_DAYS = 14
SEED = 42
START_DATE = datetime(2025, 1, 1, 23, 30, 0)


def fixtures_dir() -> Path:
    return Path(__file__).parent / "zips"


def _cycles_row(day: int, rng: random.Random) -> dict[str, str]:
    start = START_DATE + timedelta(days=day)
    end = start + timedelta(hours=10)
    sleep_min = 420 + rng.randint(0, 120)
    deep = 90 + rng.randint(0, 30)
    rem = 90 + rng.randint(0, 40)
    awake = 30 + rng.randint(0, 30)
    light = sleep_min - deep - rem
    return {
        "Cycle start time": start.strftime("%Y-%m-%d %H:%M:%S"),
        "Cycle end time": end.strftime("%Y-%m-%d %H:%M:%S"),
        "Cycle timezone": "UTC+05:00",
        "Recovery score %": str(60 + rng.randint(0, 30)),
        "Resting heart rate (bpm)": str(48 + rng.randint(0, 6)),
        "Heart rate variability (ms)": str(110 + rng.randint(0, 30)),
        "Skin temp (celsius)": f"{33.5 + rng.random():.2f}",
        "Blood oxygen %": f"{94 + rng.random() * 2:.2f}",
        "Day Strain": f"{8 + rng.random() * 6:.1f}",
        "Energy burned (cal)": str(1700 + rng.randint(0, 600)),
        "Max HR (bpm)": str(150 + rng.randint(0, 30)),
        "Average HR (bpm)": str(70 + rng.randint(0, 20)),
        "Sleep onset": start.strftime("%Y-%m-%d %H:%M:%S"),
        "Wake onset": (start + timedelta(minutes=sleep_min + awake)).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "Sleep performance %": str(75 + rng.randint(0, 20)),
        "Respiratory rate (rpm)": f"{14.5 + rng.random():.2f}",
        "Asleep duration (min)": str(sleep_min),
        "In bed duration (min)": str(sleep_min + awake),
        "Light sleep duration (min)": str(light),
        "Deep (SWS) duration (min)": str(deep),
        "REM duration (min)": str(rem),
        "Awake duration (min)": str(awake),
        "Sleep need (min)": "480",
        "Sleep debt (min)": "0",
        "Sleep efficiency %": "92",
        "Sleep consistency %": "65",
    }


def _sleeps_row_from_cycle(c: dict[str, str]) -> dict[str, str]:
    return {col: c.get(col, "") for col in SLEEPS_REQUIRED_COLUMNS} | {"Nap": "false"}


def _workout_row(day: int, rng: random.Random) -> dict[str, str]:
    start = START_DATE + timedelta(days=day, hours=14)
    end = start + timedelta(minutes=30)
    return {
        "Cycle start time": (START_DATE + timedelta(days=day)).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "Cycle end time": (START_DATE + timedelta(days=day + 1)).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "Cycle timezone": "UTC+05:00",
        "Workout start time": start.strftime("%Y-%m-%d %H:%M:%S"),
        "Workout end time": end.strftime("%Y-%m-%d %H:%M:%S"),
        "Duration (min)": "30",
        "Activity name": "Walking",
        "Activity Strain": f"{6 + rng.random() * 3:.1f}",
        "Energy burned (cal)": str(200 + rng.randint(0, 100)),
        "Max HR (bpm)": str(140 + rng.randint(0, 20)),
        "Average HR (bpm)": str(110 + rng.randint(0, 15)),
        "HR Zone 1 %": "60",
        "HR Zone 2 %": "30",
        "HR Zone 3 %": "10",
        "HR Zone 4 %": "0",
        "HR Zone 5 %": "0",
        "GPS enabled": "false",
    }


def _journal_row(day: int) -> dict[str, str]:
    cs = (START_DATE + timedelta(days=day)).strftime("%Y-%m-%d %H:%M:%S")
    return {
        "Cycle start time": cs,
        "Cycle end time": (START_DATE + timedelta(days=day + 1)).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "Cycle timezone": "UTC+05:00",
        "Question text": "Hydrated sufficiently?",
        "Answered yes": "true",
        "Notes": "",
    }


def _csv_bytes(rows: list[dict[str, str]], columns: tuple[str, ...]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(columns))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def _empty_csv_bytes(columns: tuple[str, ...]) -> bytes:
    return _csv_bytes([], columns)


def _build_zip(
    target: Path,
    days: int,
    *,
    include_workouts: bool = True,
    include_journal: bool = True,
) -> None:
    rng = random.Random(SEED)
    cycles = [_cycles_row(d, rng) for d in range(days)]
    sleeps = [_sleeps_row_from_cycle(c) for c in cycles]
    workouts = [_workout_row(d, rng) for d in range(days // 3)] if include_workouts else []
    journal = [_journal_row(d) for d in range(days // 2)] if include_journal else []

    cycles_bytes = _csv_bytes(cycles, CYCLES_REQUIRED_COLUMNS)
    sleeps_bytes = _csv_bytes(sleeps, SLEEPS_REQUIRED_COLUMNS)
    workouts_bytes = (
        _csv_bytes(workouts, WORKOUTS_REQUIRED_COLUMNS)
        if include_workouts
        else _empty_csv_bytes(WORKOUTS_REQUIRED_COLUMNS)
    )
    journal_bytes = (
        _csv_bytes(journal, JOURNAL_REQUIRED_COLUMNS)
        if include_journal
        else _empty_csv_bytes(JOURNAL_REQUIRED_COLUMNS)
    )

    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("physiological_cycles.csv", cycles_bytes)
        zf.writestr("sleeps.csv", sleeps_bytes)
        zf.writestr("workouts.csv", workouts_bytes)
        zf.writestr("journal_entries.csv", journal_bytes)


def build_corrupt_zip(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"this is not a zip file at all\x00\x01\x02")


def build_wrong_format_zip(target: Path) -> None:
    rng = random.Random(SEED)
    rows = [_cycles_row(d, rng) for d in range(5)]
    # Replace one required column name with garbage
    bad_columns = tuple(
        "Recovery_score" if c == "Recovery score %" else c
        for c in CYCLES_REQUIRED_COLUMNS
    )
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(bad_columns))
    writer.writeheader()
    for row in rows:
        renamed = {
            ("Recovery_score" if k == "Recovery score %" else k): v for k, v in row.items()
        }
        writer.writerow(renamed)
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("physiological_cycles.csv", buf.getvalue())
        zf.writestr("sleeps.csv", _empty_csv_bytes(SLEEPS_REQUIRED_COLUMNS))
        zf.writestr("workouts.csv", _empty_csv_bytes(WORKOUTS_REQUIRED_COLUMNS))
        zf.writestr("journal_entries.csv", _empty_csv_bytes(JOURNAL_REQUIRED_COLUMNS))


def build_all_fixtures() -> None:
    d = fixtures_dir()
    _build_zip(d / "happy.zip", HAPPY_DAYS, include_workouts=True, include_journal=True)
    _build_zip(d / "minimal_14d.zip", MINIMAL_DAYS)
    _build_zip(d / "no_workouts.zip", HAPPY_DAYS, include_workouts=False)
    _build_zip(d / "no_journal.zip", HAPPY_DAYS, include_journal=False)
    build_corrupt_zip(d / "corrupt.zip")
    build_wrong_format_zip(d / "wrong_format.zip")


if __name__ == "__main__":
    build_all_fixtures()
    print(f"fixtures built in {fixtures_dir()}")
