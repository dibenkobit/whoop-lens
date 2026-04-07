"""Sleep section: average bedtime/wake, stage percentages, hypnogram, consistency strip."""
import math

import pandas as pd  # pyright: ignore[reportMissingTypeStubs]

from app.analysis.time_helpers import bedtime_hour, format_clock, wake_hour
from app.models.report import (
    BedtimeStrip,
    SleepDurations,
    SleepSection,
    SleepStagePct,
)
from app.parsing.frames import ParsedFrames


def compute_sleep_section(f: ParsedFrames) -> SleepSection:
    c = f.cycles
    bed_hours = [bedtime_hour(t) for t in c["Sleep onset"].dropna()]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportUnknownArgumentType]
    wake_hours = [wake_hour(t) for t in c["Wake onset"].dropna()]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportUnknownArgumentType]
    avg_bed = sum(bed_hours) / len(bed_hours) if bed_hours else 0.0
    avg_wake = sum(wake_hours) / len(wake_hours) if wake_hours else 0.0

    if len(bed_hours) >= 2:
        mean = sum(bed_hours) / len(bed_hours)
        var = sum((x - mean) ** 2 for x in bed_hours) / (len(bed_hours) - 1)
        bed_std = math.sqrt(var)
    else:
        bed_std = 0.0

    light = float(c["Light sleep duration (min)"].dropna().mean() or 0.0)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
    rem = float(c["REM duration (min)"].dropna().mean() or 0.0)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
    deep = float(c["Deep (SWS) duration (min)"].dropna().mean() or 0.0)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
    awake = float(c["Awake duration (min)"].dropna().mean() or 0.0)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
    asleep_total = light + rem + deep
    if asleep_total > 0:
        light_pct = round(light / asleep_total * 100, 1)
        rem_pct = round(rem / asleep_total * 100, 1)
        deep_pct = round(deep / asleep_total * 100, 1)
    else:
        light_pct = rem_pct = deep_pct = 0.0

    last14 = c.tail(14)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    strip: list[BedtimeStrip] = []
    for _, row in last14.iterrows():  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        if pd.isna(row["Sleep onset"]) or pd.isna(row["Wake onset"]):  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportUnknownArgumentType, reportGeneralTypeIssues]
            continue
        strip.append(
            BedtimeStrip(
                date=row["Cycle start time"].date().isoformat(),  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAttributeAccessIssue, reportUnknownArgumentType]
                bed_local=format_clock(bedtime_hour(row["Sleep onset"])),  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType, reportArgumentType]
                wake_local=format_clock(wake_hour(row["Wake onset"])),  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType, reportArgumentType]
            )
        )

    return SleepSection(
        avg_bedtime=format_clock(avg_bed),
        avg_wake=format_clock(avg_wake),
        bedtime_std_h=round(bed_std, 2),
        avg_durations=SleepDurations(
            light_min=round(light, 1),
            rem_min=round(rem, 1),
            deep_min=round(deep, 1),
            awake_min=round(awake, 1),
        ),
        stage_pct=SleepStagePct(light=light_pct, rem=rem_pct, deep=deep_pct),
        hypnogram_sample=None,  # v1: skip; needs per-night stage timeline data
        consistency_strip=strip,
    )
