from typing import Any, Literal

from pydantic import BaseModel, model_serializer

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

    @model_serializer(mode="wrap")
    def _drop_none(self, handler: Any) -> dict[str, Any]:
        data = handler(self)
        return {k: v for k, v in data.items() if v is not None}


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

    @model_serializer(mode="wrap")
    def _drop_none(self, handler: Any) -> dict[str, Any]:
        data = handler(self)
        return {k: v for k, v in data.items() if v is not None}
