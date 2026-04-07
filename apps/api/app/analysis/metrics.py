"""Top-level aggregate metrics computed from parsed frames."""
import pandas as pd  # pyright: ignore[reportMissingTypeStubs]

from app.models.report import Metrics, Period
from app.parsing.frames import ParsedFrames


def _safe_mean(series: pd.Series, default: float = 0.0) -> float:  # pyright: ignore[reportMissingTypeStubs]
    s = series.dropna()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    return float(s.mean()) if len(s) > 0 else default  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]


def compute_period(f: ParsedFrames) -> Period:
    starts = f.cycles["Cycle start time"].dropna()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if starts.empty:  # pyright: ignore[reportUnknownMemberType]
        return Period(start="", end="", days=0)
    start = starts.min()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    end = starts.max()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    return Period(
        start=str(start.date().isoformat()),  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownArgumentType]
        end=str(end.date().isoformat()),  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownArgumentType]
        days=int((end.date() - start.date()).days) + 1,  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportOperatorIssue, reportUnknownArgumentType]
    )


def compute_metrics(f: ParsedFrames) -> Metrics:
    c = f.cycles
    return Metrics(
        hrv_ms=_safe_mean(c["Heart rate variability (ms)"]),  # pyright: ignore[reportArgumentType]
        rhr_bpm=_safe_mean(c["Resting heart rate (bpm)"]),  # pyright: ignore[reportArgumentType]
        resp_rpm=_safe_mean(c["Respiratory rate (rpm)"]),  # pyright: ignore[reportArgumentType]
        spo2_pct=_safe_mean(c["Blood oxygen %"]),  # pyright: ignore[reportArgumentType]
        sleep_efficiency_pct=_safe_mean(c["Sleep efficiency %"]),  # pyright: ignore[reportArgumentType]
        sleep_consistency_pct=_safe_mean(c["Sleep consistency %"]),  # pyright: ignore[reportArgumentType]
        sleep_debt_min=_safe_mean(c["Sleep debt (min)"]),  # pyright: ignore[reportArgumentType]
    )
