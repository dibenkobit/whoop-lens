"""Insight rules.

Each rule is a pure function `(ParsedFrames) -> Insight | None`.
Returning None means the rule didn't trigger and is dropped from the response.
"""
from collections.abc import Callable

import pandas as pd  # pyright: ignore[reportMissingTypeStubs]

from app.analysis.time_helpers import bedtime_hour
from app.models.insight import Insight, InsightHighlight
from app.parsing.frames import ParsedFrames

InsightFn = Callable[[ParsedFrames], Insight | None]


def _safe_mean(series: pd.Series) -> float | None:  # pyright: ignore[reportMissingTypeStubs]
    """Return mean of series, or None if the series has no non-null values.

    Unlike ``float(series.mean() or 0.0)``, this never conflates an empty
    series with a legitimate zero mean, and never coerces a legitimate 0.0 to
    None.
    """
    s = series.dropna()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if s.empty:  # pyright: ignore[reportUnknownMemberType]
        return None
    return float(s.mean())  # pyright: ignore[reportUnknownMemberType, reportArgumentType, reportUnknownArgumentType]


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
    rec_short = _safe_mean(rec[short_mask])  # pyright: ignore[reportUnknownVariableType, reportAttributeAccessIssue, reportUnknownArgumentType, reportArgumentType]
    rec_long = _safe_mean(rec[long_mask])  # pyright: ignore[reportUnknownVariableType, reportAttributeAccessIssue, reportUnknownArgumentType, reportArgumentType]
    long_count = int(long_mask.sum())  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
    rec_short_f: float = rec_short if rec_short is not None else 0.0
    severity = "high" if short_pct > 0.15 else "medium"
    if long_count == 0 or rec_long is None:
        # No 8+ hour nights to compare against — still fire with a simpler body.
        return Insight(
            kind="undersleep",
            severity=severity,
            title=f"You undersleep {round(short_pct * 100)}% of nights",
            body=(
                f"You sleep under 6 hours on {round(short_pct * 100)}% of nights. "
                f"That's a lot — aim for 7+ hours to give your body time to recover."
            ),
            highlight=InsightHighlight(value=f"{round(short_pct * 100)}%", unit=None),
        )
    delta = round(rec_long - rec_short_f)
    return Insight(
        kind="undersleep",
        severity=severity,
        title=f"You undersleep {round(short_pct * 100)}% of nights",
        body=(
            f"On nights under 6 hours your recovery averages {round(rec_short_f)}%; "
            f"on nights with 8+ hours it averages {round(rec_long)}%. "
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
    # Gate 1: enough bedtime variance to be worth calling out
    if median_std < 1.5:
        return None
    rec = f.cycles["Recovery score %"]  # pyright: ignore[reportUnknownVariableType]
    low_var_mask = (rolling_std < 1).reindex(rec.index, fill_value=False)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    high_var_mask = (rolling_std > 2).reindex(rec.index, fill_value=False)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    rec_low = _safe_mean(rec[low_var_mask])  # pyright: ignore[reportUnknownVariableType, reportAttributeAccessIssue, reportUnknownArgumentType, reportArgumentType]
    rec_high = _safe_mean(rec[high_var_mask])  # pyright: ignore[reportUnknownVariableType, reportAttributeAccessIssue, reportUnknownArgumentType, reportArgumentType]
    # Gate 2: both buckets must exist (can't claim a delta without both sides)
    if rec_low is None or rec_high is None:
        return None
    delta = rec_low - rec_high
    # Gate 3: plan's statistical criterion — low-var weeks must score meaningfully higher
    if delta < 5:
        return None
    delta_pp = round(delta)
    return Insight(
        kind="bedtime_consistency",
        severity="medium",
        title="Your most stable weeks score much higher",
        body=(
            f"On weeks where your bedtime is consistent (7-day std under 1h) your recovery "
            f"averages {round(rec_low)}%, versus {round(rec_high)}% on your most irregular weeks "
            f"— a {delta_pp} pp gap. Going to bed at a similar time each night pays off as much "
            f"as sleeping more."
        ),
        highlight=InsightHighlight(value=f"+{delta_pp}", unit="pp"),
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
            "Your average bedtime is past 01:00. Even with the same total sleep, "
            "earlier bedtimes (00:00-01:00) tend to score 5-10 percentage points "
            "higher in recovery."
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
            if pd.notna(v):  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                next_recoveries.append(float(v))  # pyright: ignore[reportUnknownArgumentType]
    if not next_recoveries:
        return None
    baseline = _safe_mean(c["Recovery score %"])  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
    if baseline is None:
        return None
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
            f"{round(after)}% — about {round(delta)} points below your usual baseline of "
            f"{round(baseline)}%. Consider a recovery day after strenuous efforts."
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


def insight_dow_pattern(f: ParsedFrames) -> Insight | None:
    c = f.cycles
    rec = c["Recovery score %"].dropna()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if rec.empty:  # pyright: ignore[reportUnknownMemberType]
        return None
    dow = c.loc[rec.index, "Cycle start time"].dt.day_name()  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
    by_dow = rec.groupby(dow).mean()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportUnknownArgumentType]
    if by_dow.empty:  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        return None
    best_day = by_dow.idxmax()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAttributeAccessIssue]
    worst_day = by_dow.idxmin()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAttributeAccessIssue]
    spread = float(by_dow.max() - by_dow.min())  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType, reportAttributeAccessIssue, reportCallIssue]
    if spread < 5:
        return None
    return Insight(
        kind="dow_pattern",
        severity="low",
        title=f"{worst_day} is your weakest day",
        body=(
            f"Your average recovery on {worst_day}s is {round(float(by_dow[worst_day]))}%, "  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType, reportCallIssue, reportIndexIssue]
            f"versus {round(float(by_dow[best_day]))}% on {best_day}s. "  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType, reportCallIssue, reportIndexIssue]
            f"Worth noticing what's different about that part of your week."
        ),
        highlight=InsightHighlight(value=f"-{round(spread)}", unit="pp"),
    )


def insight_sleep_stage_quality(f: ParsedFrames) -> Insight | None:
    c = f.cycles
    light = float(c["Light sleep duration (min)"].dropna().mean() or 0.0)  # pyright: ignore[reportUnknownMemberType, reportArgumentType, reportUnknownArgumentType]
    rem = float(c["REM duration (min)"].dropna().mean() or 0.0)  # pyright: ignore[reportUnknownMemberType, reportArgumentType, reportUnknownArgumentType]
    deep = float(c["Deep (SWS) duration (min)"].dropna().mean() or 0.0)  # pyright: ignore[reportUnknownMemberType, reportArgumentType, reportUnknownArgumentType]
    total = light + rem + deep
    if total == 0:
        return None
    deep_pct = deep / total * 100
    rem_pct = rem / total * 100
    if max(deep_pct, rem_pct) < 20:
        return None
    return Insight(
        kind="sleep_stage_quality",
        severity="low",
        title="Your sleep architecture is excellent",
        body=(
            f"Average deep sleep is {round(deep_pct)}% and REM is {round(rem_pct)}% of "
            f"total sleep — both above typical adult baselines (around 13-18% for deep). "
            f"Your body is doing the recovery work it should."
        ),
        highlight=InsightHighlight(value=f"{round(deep_pct)}%", unit="deep"),
    )


def insight_long_term_trend(f: ParsedFrames) -> Insight | None:
    c = f.cycles.sort_values("Cycle start time").reset_index(drop=True)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if len(c) < 120:  # pyright: ignore[reportUnknownArgumentType]
        return None
    first = c.head(60)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    last = c.tail(60)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

    def _col_mean(df: pd.DataFrame, col: str) -> float | None:
        return _safe_mean(df[col])  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportUnknownArgumentType, reportArgumentType]

    rhr_first = _col_mean(first, "Resting heart rate (bpm)")
    rhr_last = _col_mean(last, "Resting heart rate (bpm)")
    sleep_first = _col_mean(first, "Asleep duration (min)")
    sleep_last = _col_mean(last, "Asleep duration (min)")
    rec_first = _col_mean(first, "Recovery score %")
    rec_last = _col_mean(last, "Recovery score %")
    if any(v is None for v in (rhr_first, rhr_last, sleep_first, sleep_last, rec_first, rec_last)):
        return None
    # All values confirmed non-None above; cast to float for arithmetic
    rhr_first_f = float(rhr_first)  # type: ignore[arg-type]
    rhr_last_f = float(rhr_last)  # type: ignore[arg-type]
    sleep_first_f = float(sleep_first)  # type: ignore[arg-type]
    sleep_last_f = float(sleep_last)  # type: ignore[arg-type]
    rec_first_f = float(rec_first)  # type: ignore[arg-type]
    rec_last_f = float(rec_last)  # type: ignore[arg-type]
    rhr_delta = rhr_first_f - rhr_last_f
    sleep_delta = (sleep_last_f - sleep_first_f) / 60
    rec_delta = rec_last_f - rec_first_f
    improvements = sum(
        1
        for v in (rhr_delta, sleep_delta, rec_delta)
        if v > 0
    )
    if improvements < 2:
        return None
    return Insight(
        kind="long_term_trend",
        severity="low",
        title="You're trending in the right direction",
        body=(
            f"Comparing your first 60 days to your last 60: resting HR is "
            f"{abs(round(rhr_delta, 1))} bpm {'lower' if rhr_delta > 0 else 'higher'}, "
            f"average sleep is {abs(round(sleep_delta, 1))}h "
            f"{'longer' if sleep_delta > 0 else 'shorter'}, and recovery is "
            f"{abs(round(rec_delta))} pp {'higher' if rec_delta > 0 else 'lower'}."
        ),
        highlight=InsightHighlight(value=f"+{round(rec_delta)}", unit="pp"),
    )


def insight_workout_mix(f: ParsedFrames) -> Insight | None:
    if f.workouts.empty:
        return None
    total = float(f.workouts["Activity Strain"].dropna().sum() or 0.0)  # pyright: ignore[reportUnknownMemberType, reportArgumentType, reportUnknownArgumentType]
    if total == 0:
        return None
    _walking_raw = (  # pyright: ignore[reportUnknownVariableType]
        f.workouts.loc[
            f.workouts["Activity name"].isin(["Walking", "Activity"]), "Activity Strain"  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        ]
        .dropna()  # pyright: ignore[reportUnknownMemberType]
        .sum()  # pyright: ignore[reportUnknownMemberType]
        or 0.0
    )
    walking_strain = float(_walking_raw)  # pyright: ignore[reportArgumentType, reportUnknownArgumentType]
    pct = walking_strain / total * 100
    if pct < 50:
        return None
    return Insight(
        kind="workout_mix",
        severity="low",
        title="Most of your strain is steady-state",
        body=(
            f"Walking and general activity make up {round(pct)}% of your total strain. "
            f"Adding even one or two strength or interval sessions per week would diversify "
            f"the load."
        ),
        highlight=InsightHighlight(value=f"{round(pct)}%"),
    )


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
