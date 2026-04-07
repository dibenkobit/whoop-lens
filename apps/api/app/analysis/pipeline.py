"""Orchestrate parsed frames → WhoopReport."""
from app.analysis.insights import run_insight_rules
from app.analysis.metrics import compute_metrics, compute_period
from app.analysis.sleep import compute_sleep_section
from app.analysis.strain import compute_strain_section, compute_workouts_section
from app.analysis.trends import (
    compute_dials,
    compute_recovery_section,
    compute_trends_section,
)
from app.models.report import JournalSection, WhoopReport
from app.parsing.frames import ParsedFrames


def _compute_journal_section(f: ParsedFrames) -> JournalSection | None:
    j = f.journal
    if j.empty:
        return None
    days = j["Cycle start time"].nunique()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    questions: list[dict[str, object]] = []
    for q, sub in j.groupby("Question text"):  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        yes = int((sub["Answered yes"] == "true").sum())  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
        no = int((sub["Answered yes"] == "false").sum())  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportArgumentType, reportUnknownArgumentType]
        questions.append(
            {
                "question": str(q),
                "yes": yes,
                "no": no,
                "mean_rec_yes": None,
                "mean_rec_no": None,
            }
        )
    note = (
        f"{int(days)} days logged. "  # pyright: ignore[reportArgumentType]
        + ("Sample too small for statistical conclusions." if days < 30 else "")  # pyright: ignore[reportOperatorIssue]
    ).strip()
    return JournalSection.model_validate(
        {"days_logged": int(days), "questions": questions, "note": note}  # pyright: ignore[reportArgumentType]
    )


def build_report(f: ParsedFrames) -> WhoopReport:
    return WhoopReport(
        schema_version=1,
        period=compute_period(f),
        dials=compute_dials(f),
        metrics=compute_metrics(f),
        recovery=compute_recovery_section(f),
        sleep=compute_sleep_section(f),
        strain=compute_strain_section(f),
        workouts=compute_workouts_section(f),
        journal=_compute_journal_section(f),
        trends=compute_trends_section(f),
        insights=run_insight_rules(f),
    )
