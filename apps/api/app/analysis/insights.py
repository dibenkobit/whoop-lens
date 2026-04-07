"""Insight rules.

Each rule is a pure function `(ParsedFrames) -> Insight | None`.
Returning None means the rule didn't trigger and is dropped from the response.
"""
import math
from collections.abc import Callable

from app.analysis.time_helpers import bedtime_hour
from app.models.insight import Insight, InsightHighlight
from app.parsing.frames import ParsedFrames

InsightFn = Callable[[ParsedFrames], Insight | None]


def insight_undersleep(f: ParsedFrames) -> Insight | None:
    sleep_h = f.cycles["Asleep duration (min)"].dropna() / 60  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if sleep_h.empty:  # pyright: ignore[reportUnknownMemberType]
        return None
    short_pct = float((sleep_h < 6).mean())  # pyright: ignore[reportUnknownMemberType, reportArgumentType, reportUnknownArgumentType]
    if short_pct < 0.05:
        return None
    rec = f.cycles["Recovery score %"]  # pyright: ignore[reportUnknownVariableType]
    short_mask = (sleep_h < 6).reindex(f.cycles.index, fill_value=False)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    long_mask = (sleep_h >= 8).reindex(f.cycles.index, fill_value=False)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    rec_short_raw = rec[short_mask].dropna().mean()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAttributeAccessIssue]
    rec_long_raw = rec[long_mask].dropna().mean()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAttributeAccessIssue]
    rec_short_f: float = float(rec_short_raw) if rec_short_raw is not None and not math.isnan(float(rec_short_raw)) else 0.0  # pyright: ignore[reportArgumentType, reportUnknownArgumentType]
    rec_long_f: float = float(rec_long_raw) if rec_long_raw is not None and not math.isnan(float(rec_long_raw)) else 0.0  # pyright: ignore[reportArgumentType, reportUnknownArgumentType]
    delta = round(rec_long_f - rec_short_f)
    severity = "high" if short_pct > 0.15 else "medium"
    return Insight(
        kind="undersleep",
        severity=severity,
        title=f"You undersleep {round(short_pct * 100)}% of nights",
        body=(
            f"On nights under 6 hours your recovery averages {round(rec_short_f)}%; "
            f"on nights with 8+ hours it averages {round(rec_long_f)}%. "
            f"Adding sleep is your single biggest lever."
        ),
        highlight=InsightHighlight(value=f"+{delta}", unit="pp"),
    )


def insight_bedtime_consistency(f: ParsedFrames) -> Insight | None:
    onsets = f.cycles["Sleep onset"].dropna()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if len(onsets) < 14:  # pyright: ignore[reportUnknownArgumentType]
        return None
    bed_h = onsets.apply(bedtime_hour)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportUnknownArgumentType]
    rolling_std = bed_h.rolling(7, min_periods=4).std().dropna()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if rolling_std.empty:  # pyright: ignore[reportUnknownMemberType]
        return None
    median_std = float(rolling_std.median())  # pyright: ignore[reportUnknownMemberType, reportArgumentType, reportUnknownArgumentType]
    if median_std < 1.5:
        return None
    rec = f.cycles["Recovery score %"]  # pyright: ignore[reportUnknownVariableType]
    low_var_mask = (rolling_std < 1).reindex(rec.index, fill_value=False)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    high_var_mask = (rolling_std > 2).reindex(rec.index, fill_value=False)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    rec_low_raw = rec[low_var_mask].dropna().mean()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAttributeAccessIssue]
    rec_high_raw = rec[high_var_mask].dropna().mean()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAttributeAccessIssue]
    rec_low_f: float = float(rec_low_raw) if rec_low_raw is not None and not math.isnan(float(rec_low_raw)) else 0.0  # pyright: ignore[reportArgumentType, reportUnknownArgumentType]
    rec_high_f: float = float(rec_high_raw) if rec_high_raw is not None and not math.isnan(float(rec_high_raw)) else 0.0  # pyright: ignore[reportArgumentType, reportUnknownArgumentType]
    delta = round(rec_low_f - rec_high_f)
    return Insight(
        kind="bedtime_consistency",
        severity="medium",
        title="Your most stable weeks score much higher",
        body=(
            f"Irregular bedtimes (7-day std {round(median_std, 1)}h) are linked to "
            f"lower recovery. Going to bed at a similar time pays off as much as sleeping more."
        ),
        highlight=InsightHighlight(value=f"+{delta}", unit="pp"),
    )


def insight_late_chronotype(f: ParsedFrames) -> Insight | None:
    onsets = f.cycles["Sleep onset"].dropna()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if len(onsets) < 14:  # pyright: ignore[reportUnknownArgumentType]
        return None
    bed_h = [bedtime_hour(t) for t in onsets]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
    avg_bed = sum(bed_h) / len(bed_h)
    if avg_bed < 25.0:  # earlier than 01:00
        return None
    return Insight(
        kind="late_chronotype",
        severity="low",
        title="You're a strong night owl",
        body=(
            f"Your average bedtime is past 01:00. Even with the same total sleep, "
            f"earlier bedtimes (00:00–01:00) tend to score 5-10 percentage points "
            f"higher in recovery."
        ),
        highlight=InsightHighlight(value="01:00+"),
    )


def insight_overtraining(f: ParsedFrames) -> Insight | None:
    c = f.cycles.sort_values("Cycle start time").reset_index(drop=True)
    if len(c) < 5:
        return None
    high_strain_idx = c.index[c["Day Strain"] > 15].tolist()  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
    if not high_strain_idx:
        return None
    next_recoveries: list[float] = []
    for i in high_strain_idx:  # pyright: ignore[reportUnknownVariableType]
        if i + 1 < len(c):
            v = c.loc[i + 1, "Recovery score %"]  # pyright: ignore[reportUnknownVariableType]
            if v is not None:
                next_recoveries.append(float(v))  # pyright: ignore[reportUnknownArgumentType]
    if not next_recoveries:
        return None
    baseline = float(c["Recovery score %"].dropna().mean() or 0.0)  # pyright: ignore[reportUnknownMemberType, reportArgumentType, reportUnknownArgumentType]
    after = sum(next_recoveries) / len(next_recoveries)
    delta = baseline - after
    if delta < 5:
        return None
    return Insight(
        kind="overtraining",
        severity="medium",
        title="Big strain days drag the next day",
        body=(
            f"After days with strain over 15, your recovery the next morning averages "
            f"{round(after)}% — about {round(delta)} points below your usual baseline of {round(baseline)}%. "
            f"Consider a recovery day after strenuous efforts."
        ),
        highlight=InsightHighlight(value=f"-{round(delta)}", unit="pp"),
    )


def insight_sick_episodes(f: ParsedFrames) -> Insight | None:
    c = f.cycles
    if c["Recovery score %"].dropna().empty:  # pyright: ignore[reportUnknownMemberType]
        return None
    hrv_med = float(c["Heart rate variability (ms)"].median())  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportArgumentType]
    rhr_med = float(c["Resting heart rate (bpm)"].median())  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportArgumentType]
    mask = (  # pyright: ignore[reportUnknownVariableType]
        (c["Recovery score %"] < 30)
        & (c["Heart rate variability (ms)"] < hrv_med * 0.7)
        & (c["Resting heart rate (bpm)"] > rhr_med * 1.15)
    )
    n = int(mask.sum())  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
    if n == 0:
        return None
    return Insight(
        kind="sick_episodes",
        severity="low",
        title=f"{n} likely illness day{'s' if n > 1 else ''} detected",
        body=(
            "On these days HRV crashed, resting heart rate spiked, and recovery dropped "
            "below 30 — typical signs your body is fighting something. Rest is the right "
            "call."
        ),
        highlight=InsightHighlight(value=str(n)),
    )


def insight_travel_impact(f: ParsedFrames) -> Insight | None:
    c = f.cycles
    tzs = c["Cycle timezone"].dropna()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if tzs.empty:  # pyright: ignore[reportUnknownMemberType]
        return None
    home_tz = tzs.value_counts().idxmax()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    away_mask = c["Cycle timezone"] != home_tz  # pyright: ignore[reportUnknownVariableType]
    if away_mask.sum() < 3:  # pyright: ignore[reportUnknownMemberType]
        return None
    rec_home = float(c.loc[~away_mask, "Recovery score %"].dropna().mean() or 0.0)  # pyright: ignore[reportUnknownMemberType, reportArgumentType, reportUnknownArgumentType]
    rec_away = float(c.loc[away_mask, "Recovery score %"].dropna().mean() or 0.0)  # pyright: ignore[reportUnknownMemberType, reportArgumentType, reportUnknownArgumentType]
    delta = rec_home - rec_away
    if delta < 3:
        return None
    return Insight(
        kind="travel_impact",
        severity="medium",
        title="Travel hits your recovery",
        body=(
            f"You spent {int(away_mask.sum())} days outside your home timezone "  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
            f"({home_tz}). Recovery dropped from {round(rec_home)}% at home to "
            f"{round(rec_away)}% on the road."
        ),
        highlight=InsightHighlight(value=f"-{round(delta)}", unit="pp"),
    )


def insight_dow_pattern(_f: ParsedFrames) -> Insight | None:
    return None


def insight_sleep_stage_quality(_f: ParsedFrames) -> Insight | None:
    return None


def insight_long_term_trend(_f: ParsedFrames) -> Insight | None:
    return None


def insight_workout_mix(_f: ParsedFrames) -> Insight | None:
    return None


INSIGHT_RULES: list[InsightFn] = [
    insight_undersleep,
    insight_bedtime_consistency,
    insight_late_chronotype,
    insight_overtraining,
    insight_sick_episodes,
    insight_travel_impact,
    insight_dow_pattern,
    insight_sleep_stage_quality,
    insight_long_term_trend,
    insight_workout_mix,
]


def run_insight_rules(f: ParsedFrames) -> list[Insight]:
    results: list[Insight] = []
    for rule in INSIGHT_RULES:
        out = rule(f)
        if out is not None:
            results.append(out)
    return results
