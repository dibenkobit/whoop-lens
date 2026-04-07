from typing import Literal

from pydantic import BaseModel

InsightKind = Literal[
    "undersleep",
    "bedtime_consistency",
    "late_chronotype",
    "overtraining",
    "sick_episodes",
    "travel_impact",
    "dow_pattern",
    "sleep_stage_quality",
    "long_term_trend",
    "workout_mix",
]

InsightSeverity = Literal["low", "medium", "high"]


class InsightHighlight(BaseModel):
    value: str
    unit: str | None = None


class InsightEvidence(BaseModel):
    value: float
    label: str


class Insight(BaseModel):
    kind: InsightKind
    severity: InsightSeverity
    title: str
    body: str
    highlight: InsightHighlight
    evidence: list[InsightEvidence] | None = None
