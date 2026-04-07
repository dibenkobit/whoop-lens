"""Strain section + workouts section."""
import pandas as pd  # pyright: ignore[reportMissingTypeStubs]

from app.models.report import (
    ActivityAgg,
    StrainDistribution,
    StrainSection,
    TopStrainDay,
    TrendPoint,
    WorkoutsSection,
)
from app.parsing.frames import ParsedFrames


def compute_strain_section(f: ParsedFrames) -> StrainSection:
    c = f.cycles
    strains = c["Day Strain"].dropna()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    n = max(len(strains), 1)  # pyright: ignore[reportUnknownArgumentType]
    dist = StrainDistribution(
        light=round(float((strains < 10).sum()) / n * 100, 1),  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportOperatorIssue, reportArgumentType, reportUnknownArgumentType]
        moderate=round(float(((strains >= 10) & (strains < 14)).sum()) / n * 100, 1),  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportOperatorIssue, reportArgumentType, reportUnknownArgumentType]
        high=round(float(((strains >= 14) & (strains < 18)).sum()) / n * 100, 1),  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportOperatorIssue, reportArgumentType, reportUnknownArgumentType]
        all_out=round(float((strains >= 18).sum()) / n * 100, 1),  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportOperatorIssue, reportArgumentType, reportUnknownArgumentType]
    )

    trend: list[TrendPoint] = []
    for _, row in c.iterrows():  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        ts = row["Cycle start time"]  # pyright: ignore[reportUnknownVariableType]
        if pd.isna(ts):  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType, reportGeneralTypeIssues]
            continue
        v = row["Day Strain"]  # pyright: ignore[reportUnknownVariableType]
        trend.append(
            TrendPoint(date=ts.date().isoformat(), value=None if pd.isna(v) else float(v))  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownArgumentType, reportArgumentType, reportGeneralTypeIssues]
        )

    return StrainSection(
        avg_strain=round(float(strains.mean() or 0.0), 1),  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportUnknownArgumentType, reportArgumentType]
        distribution=dist,
        trend=trend,
    )


def compute_workouts_section(f: ParsedFrames) -> WorkoutsSection | None:
    w = f.workouts
    if w.empty:  # pyright: ignore[reportUnknownMemberType]
        return None

    by_activity_records: list[ActivityAgg] = []
    total_strain_all = float(w["Activity Strain"].dropna().sum() or 0.0)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
    for activity, sub in w.groupby("Activity name"):  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        total_strain = float(sub["Activity Strain"].dropna().sum() or 0.0)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
        by_activity_records.append(
            ActivityAgg(
                name=str(activity),
                count=len(sub),
                total_strain=round(total_strain, 1),
                total_min=round(float(sub["Duration (min)"].dropna().sum() or 0.0), 1),  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
                pct_of_total_strain=round(
                    total_strain / total_strain_all * 100 if total_strain_all > 0 else 0.0,
                    1,
                ),
            )
        )
    by_activity_records.sort(key=lambda a: a.total_strain, reverse=True)

    c = f.cycles.sort_values("Cycle start time").reset_index(drop=True)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    top_records: list[TopStrainDay] = []
    top10 = c.nlargest(10, "Day Strain")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    for idx, row in top10.iterrows():  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        next_idx = int(idx) + 1  # pyright: ignore[reportArgumentType]
        next_row = c.iloc[next_idx] if next_idx < len(c) else None  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        next_recovery = (
            float(next_row["Recovery score %"])  # pyright: ignore[reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
            if next_row is not None and not pd.isna(next_row["Recovery score %"])  # pyright: ignore[reportUnknownVariableType, reportArgumentType, reportUnknownMemberType, reportGeneralTypeIssues, reportUnknownArgumentType]
            else None
        )
        top_records.append(
            TopStrainDay(
                date=row["Cycle start time"].date().isoformat(),  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType, reportUnknownArgumentType]
                day_strain=round(float(row["Day Strain"]), 1),  # pyright: ignore[reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
                recovery=float(row["Recovery score %"])  # pyright: ignore[reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
                if not pd.isna(row["Recovery score %"])  # pyright: ignore[reportUnknownVariableType, reportArgumentType, reportUnknownMemberType, reportGeneralTypeIssues]
                else 0.0,
                next_recovery=next_recovery,
            )
        )

    return WorkoutsSection(
        total=len(w),
        by_activity=by_activity_records,
        top_strain_days=top_records,
    )
