from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.insight import Insight


class Period(BaseModel):
    start: str  # ISO 8601 date
    end: str
    days: int


class SleepDial(BaseModel):
    value: float
    unit: Literal["h"] = "h"
    performance_pct: float


class RecoveryDial(BaseModel):
    value: float
    unit: Literal["%"] = "%"
    green_pct: float


class StrainDial(BaseModel):
    value: float
    unit: Literal[""] = ""
    label: Literal["light", "moderate", "high", "all_out"]


class Dials(BaseModel):
    sleep: SleepDial
    recovery: RecoveryDial
    strain: StrainDial


class Metrics(BaseModel):
    hrv_ms: float
    rhr_bpm: float
    resp_rpm: float
    spo2_pct: float
    sleep_efficiency_pct: float
    sleep_consistency_pct: float
    sleep_debt_min: float


class TrendPoint(BaseModel):
    date: str  # ISO date
    value: float | None


DowName = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class DowEntry(BaseModel):
    dow: DowName
    mean: float
    n: int


class SickEpisode(BaseModel):
    date: str
    recovery: float
    rhr: float
    hrv: float
    skin_temp_c: float | None


class RecoveryDistribution(BaseModel):
    green: float
    yellow: float
    red: float


class RecoverySection(BaseModel):
    trend: list[TrendPoint]
    by_dow: list[DowEntry]
    distribution: RecoveryDistribution
    sick_episodes: list[SickEpisode]


class HypnogramSegment(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    stage: Literal["awake", "light", "rem", "deep"]
    from_: str = Field(
        ...,
        validation_alias=AliasChoices("from", "from_"),
        serialization_alias="from",
    )
    to: str


class HypnogramNight(BaseModel):
    start: str
    end: str
    segments: list[HypnogramSegment]


class BedtimeStrip(BaseModel):
    date: str
    bed_local: str  # "HH:MM"
    wake_local: str


class SleepDurations(BaseModel):
    light_min: float
    rem_min: float
    deep_min: float
    awake_min: float


class SleepStagePct(BaseModel):
    light: float
    rem: float
    deep: float


class SleepSection(BaseModel):
    avg_bedtime: str  # "HH:MM"
    avg_wake: str
    bedtime_std_h: float
    avg_durations: SleepDurations
    stage_pct: SleepStagePct
    hypnogram_sample: HypnogramNight | None
    consistency_strip: list[BedtimeStrip]


class StrainDistribution(BaseModel):
    light: float
    moderate: float
    high: float
    all_out: float


class StrainSection(BaseModel):
    avg_strain: float
    distribution: StrainDistribution
    trend: list[TrendPoint]


class ActivityAgg(BaseModel):
    name: str
    count: int
    total_strain: float
    total_min: float
    pct_of_total_strain: float


class TopStrainDay(BaseModel):
    date: str
    day_strain: float
    recovery: float
    next_recovery: float | None


class WorkoutsSection(BaseModel):
    total: int
    by_activity: list[ActivityAgg]
    top_strain_days: list[TopStrainDay]


class JournalQuestionAgg(BaseModel):
    question: str
    yes: int
    no: int
    mean_rec_yes: float | None
    mean_rec_no: float | None


class JournalSection(BaseModel):
    days_logged: int
    questions: list[JournalQuestionAgg]
    note: str


class MonthlyAgg(BaseModel):
    month: str  # "YYYY-MM"
    recovery: float
    hrv: float
    rhr: float
    sleep_h: float


class TrendComparison(BaseModel):
    # tuples are (first_60d_value, last_60d_value)
    bedtime_h: tuple[float, float]
    sleep_h: tuple[float, float]
    rhr: tuple[float, float]
    workouts: tuple[int, int]


class TrendsSection(BaseModel):
    monthly: list[MonthlyAgg]
    first_vs_last_60d: TrendComparison


class WhoopReport(BaseModel):
    schema_version: Literal[1] = 1
    period: Period
    dials: Dials
    metrics: Metrics
    recovery: RecoverySection
    sleep: SleepSection
    strain: StrainSection
    workouts: WorkoutsSection | None
    journal: JournalSection | None
    trends: TrendsSection
    insights: list[Insight]
