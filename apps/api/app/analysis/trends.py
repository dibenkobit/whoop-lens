"""Day-of-week, monthly, dial values, and trend comparisons."""
from typing import Literal

import pandas as pd  # pyright: ignore[reportMissingTypeStubs]

from app.models.report import (
    Dials,
    DowEntry,
    MonthlyAgg,
    RecoveryDial,
    RecoveryDistribution,
    RecoverySection,
    SickEpisode,
    SleepDial,
    StrainDial,
    TrendComparison,
    TrendPoint,
    TrendsSection,
)
from app.parsing.frames import ParsedFrames

DowName = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
_DOW_ORDER: tuple[DowName, ...] = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _strain_label(value: float) -> Literal["light", "moderate", "high", "all_out"]:
    if value < 10:
        return "light"
    if value < 14:
        return "moderate"
    if value < 18:
        return "high"
    return "all_out"


def compute_dials(f: ParsedFrames) -> Dials:
    c = f.cycles
    sleep_h_mean = float(c["Asleep duration (min)"].dropna().mean() / 60.0) if not c.empty else 0.0  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportOperatorIssue, reportArgumentType, reportUnknownArgumentType]
    sleep_perf_mean = float(c["Sleep performance %"].dropna().mean()) if not c.empty else 0.0  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
    rec_mean = float(c["Recovery score %"].dropna().mean()) if not c.empty else 0.0  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
    rec_green_pct = float((c["Recovery score %"].dropna() >= 67).mean() * 100) if not c.empty else 0.0  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportOperatorIssue, reportArgumentType, reportUnknownArgumentType]
    strain_mean = float(c["Day Strain"].dropna().mean()) if not c.empty else 0.0  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
    return Dials(
        sleep=SleepDial(value=round(sleep_h_mean, 2), performance_pct=round(sleep_perf_mean, 1)),
        recovery=RecoveryDial(value=round(rec_mean, 1), green_pct=round(rec_green_pct, 1)),
        strain=StrainDial(value=round(strain_mean, 1), label=_strain_label(strain_mean)),
    )


def compute_recovery_section(f: ParsedFrames) -> RecoverySection:
    c = f.cycles
    trend: list[TrendPoint] = []
    for _, row in c.iterrows():  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        ts = row["Cycle start time"]  # pyright: ignore[reportUnknownVariableType]
        if pd.isna(ts):  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType, reportGeneralTypeIssues]
            continue
        v = row["Recovery score %"]  # pyright: ignore[reportUnknownVariableType]
        trend.append(
            TrendPoint(date=ts.date().isoformat(), value=None if pd.isna(v) else float(v))  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownArgumentType, reportArgumentType, reportGeneralTypeIssues]
        )

    dow_series = c["Cycle start time"].dt.day_name().str.lower().str[:3]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAttributeAccessIssue]
    by_dow_records: list[DowEntry] = []
    for dow in _DOW_ORDER:
        sub = c[dow_series == dow]  # pyright: ignore[reportUnknownVariableType, reportArgumentType]
        rec = sub["Recovery score %"].dropna()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportAttributeAccessIssue]
        by_dow_records.append(
            DowEntry(dow=dow, mean=round(float(rec.mean() if len(rec) else 0.0), 1), n=int(len(rec)))  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportUnknownArgumentType, reportArgumentType]
        )

    rec = c["Recovery score %"].dropna()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    n = max(len(rec), 1)  # pyright: ignore[reportUnknownArgumentType]
    distribution = RecoveryDistribution(
        green=round(float((rec >= 67).sum()) / n * 100, 1),  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportOperatorIssue, reportArgumentType, reportUnknownArgumentType]
        yellow=round(float(((rec >= 34) & (rec < 67)).sum()) / n * 100, 1),  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportOperatorIssue, reportArgumentType, reportUnknownArgumentType]
        red=round(float((rec < 34).sum()) / n * 100, 1),  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportOperatorIssue, reportArgumentType, reportUnknownArgumentType]
    )

    sick_episodes: list[SickEpisode] = []
    if not rec.empty:  # pyright: ignore[reportUnknownMemberType]
        hrv_med = float(c["Heart rate variability (ms)"].median())  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
        rhr_med = float(c["Resting heart rate (bpm)"].median())  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
        mask = (  # pyright: ignore[reportUnknownVariableType]
            (c["Recovery score %"] < 30)
            & (c["Heart rate variability (ms)"] < hrv_med * 0.7)  # pyright: ignore[reportOperatorIssue]
            & (c["Resting heart rate (bpm)"] > rhr_med * 1.15)  # pyright: ignore[reportOperatorIssue]
        )
        for _, row in c[mask].iterrows():  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType]
            sick_episodes.append(
                SickEpisode(
                    date=row["Cycle start time"].date().isoformat(),  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType, reportUnknownArgumentType]
                    recovery=float(row["Recovery score %"]),  # pyright: ignore[reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
                    rhr=float(row["Resting heart rate (bpm)"]),  # pyright: ignore[reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
                    hrv=float(row["Heart rate variability (ms)"]),  # pyright: ignore[reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
                    skin_temp_c=None
                    if pd.isna(row["Skin temp (celsius)"])  # pyright: ignore[reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType, reportUnknownMemberType, reportGeneralTypeIssues]
                    else float(row["Skin temp (celsius)"]),  # pyright: ignore[reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
                )
            )

    return RecoverySection(
        trend=trend,
        by_dow=by_dow_records,
        distribution=distribution,
        sick_episodes=sick_episodes,
    )


def compute_trends_section(f: ParsedFrames) -> TrendsSection:
    c = f.cycles.copy()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    c["__month"] = c["Cycle start time"].dt.strftime("%Y-%m")  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
    monthly_records: list[MonthlyAgg] = []
    for month, sub in c.groupby("__month"):  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        monthly_records.append(
            MonthlyAgg(
                month=str(month),
                recovery=round(float(sub["Recovery score %"].dropna().mean() or 0.0), 1),  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
                hrv=round(float(sub["Heart rate variability (ms)"].dropna().mean() or 0.0), 1),  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
                rhr=round(float(sub["Resting heart rate (bpm)"].dropna().mean() or 0.0), 1),  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
                sleep_h=round(
                    float((sub["Asleep duration (min)"].dropna() / 60).mean() or 0.0), 2  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportOperatorIssue, reportArgumentType, reportUnknownArgumentType]
                ),
            )
        )

    first = c.head(60)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    last = c.tail(60)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

    def _bed_h(df: pd.DataFrame) -> float:  # pyright: ignore[reportMissingTypeStubs]
        from app.analysis.time_helpers import bedtime_hour
        vals = [bedtime_hour(t) for t in df["Sleep onset"].dropna()]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportUnknownArgumentType]
        return round(sum(vals) / len(vals), 2) if vals else 0.0

    def _sleep_h(df: pd.DataFrame) -> float:  # pyright: ignore[reportMissingTypeStubs]
        s = df["Asleep duration (min)"].dropna() / 60  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportOperatorIssue]
        return round(float(s.mean()) if len(s) else 0.0, 2)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportUnknownArgumentType, reportArgumentType]

    def _rhr(df: pd.DataFrame) -> float:  # pyright: ignore[reportMissingTypeStubs]
        s = df["Resting heart rate (bpm)"].dropna()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        return round(float(s.mean()) if len(s) else 0.0, 1)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportUnknownArgumentType, reportArgumentType]

    cmp = TrendComparison(
        bedtime_h=(_bed_h(first), _bed_h(last)),
        sleep_h=(_sleep_h(first), _sleep_h(last)),
        rhr=(_rhr(first), _rhr(last)),
        workouts=(0, 0),  # filled in by strain.py downstream if needed
    )

    return TrendsSection(monthly=monthly_records, first_vs_last_60d=cmp)
