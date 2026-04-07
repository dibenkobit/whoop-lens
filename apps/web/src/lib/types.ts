/**
 * Hand-written mirror of apps/api/app/models/*.
 * When you change one, change BOTH. Drift is a bug.
 */

export type InsightKind =
  | "undersleep"
  | "bedtime_consistency"
  | "late_chronotype"
  | "overtraining"
  | "sick_episodes"
  | "travel_impact"
  | "dow_pattern"
  | "sleep_stage_quality"
  | "long_term_trend"
  | "workout_mix";

export type InsightSeverity = "low" | "medium" | "high";

export type InsightHighlight = {
  value: string;
  unit?: string;
};

export type InsightEvidence = {
  value: number;
  label: string;
};

export type Insight = {
  kind: InsightKind;
  severity: InsightSeverity;
  title: string;
  body: string;
  highlight: InsightHighlight;
  evidence?: InsightEvidence[];
};

export type Period = {
  start: string; // ISO date
  end: string;
  days: number;
};

export type SleepDial = {
  value: number;
  unit: "h";
  performance_pct: number;
};

export type RecoveryDial = {
  value: number;
  unit: "%";
  green_pct: number;
};

export type StrainDial = {
  value: number;
  unit: "";
  label: "light" | "moderate" | "high" | "all_out";
};

export type Dials = {
  sleep: SleepDial;
  recovery: RecoveryDial;
  strain: StrainDial;
};

export type Metrics = {
  hrv_ms: number;
  rhr_bpm: number;
  resp_rpm: number;
  spo2_pct: number;
  sleep_efficiency_pct: number;
  sleep_consistency_pct: number;
  sleep_debt_min: number;
};

export type TrendPoint = { date: string; value: number | null };

export type DowName = "mon" | "tue" | "wed" | "thu" | "fri" | "sat" | "sun";

export type DowEntry = { dow: DowName; mean: number; n: number };

export type SickEpisode = {
  date: string;
  recovery: number;
  rhr: number;
  hrv: number;
  skin_temp_c: number | null;
};

export type RecoveryDistribution = {
  green: number;
  yellow: number;
  red: number;
};

export type RecoverySection = {
  trend: TrendPoint[];
  by_dow: DowEntry[];
  distribution: RecoveryDistribution;
  sick_episodes: SickEpisode[];
};

export type HypnogramStage = "awake" | "light" | "rem" | "deep";

export type HypnogramSegment = {
  stage: HypnogramStage;
  from: string; // ISO datetime (note: wire key is "from", not "from_")
  to: string;
};

export type HypnogramNight = {
  start: string;
  end: string;
  segments: HypnogramSegment[];
};

export type BedtimeStrip = {
  date: string;
  bed_local: string; // "HH:MM"
  wake_local: string;
};

export type SleepDurations = {
  light_min: number;
  rem_min: number;
  deep_min: number;
  awake_min: number;
};

export type SleepStagePct = {
  light: number;
  rem: number;
  deep: number;
};

export type SleepSection = {
  avg_bedtime: string; // "HH:MM"
  avg_wake: string;
  bedtime_std_h: number;
  avg_durations: SleepDurations;
  stage_pct: SleepStagePct;
  hypnogram_sample: HypnogramNight | null;
  consistency_strip: BedtimeStrip[];
};

export type StrainDistribution = {
  light: number;
  moderate: number;
  high: number;
  all_out: number;
};

export type StrainSection = {
  avg_strain: number;
  distribution: StrainDistribution;
  trend: TrendPoint[];
};

export type ActivityAgg = {
  name: string;
  count: number;
  total_strain: number;
  total_min: number;
  pct_of_total_strain: number;
};

export type TopStrainDay = {
  date: string;
  day_strain: number;
  recovery: number;
  next_recovery: number | null;
};

export type WorkoutsSection = {
  total: number;
  by_activity: ActivityAgg[];
  top_strain_days: TopStrainDay[];
};

export type JournalQuestionAgg = {
  question: string;
  yes: number;
  no: number;
  mean_rec_yes: number | null;
  mean_rec_no: number | null;
};

export type JournalSection = {
  days_logged: number;
  questions: JournalQuestionAgg[];
  note: string;
};

export type MonthlyAgg = {
  month: string; // "YYYY-MM"
  recovery: number;
  hrv: number;
  rhr: number;
  sleep_h: number;
};

export type TrendComparison = {
  bedtime_h: [number, number]; // [first_60d, last_60d]
  sleep_h: [number, number];
  rhr: [number, number];
  workouts: [number, number];
};

export type TrendsSection = {
  monthly: MonthlyAgg[];
  first_vs_last_60d: TrendComparison;
};

export type WhoopReport = {
  schema_version: 1;
  period: Period;
  dials: Dials;
  metrics: Metrics;
  recovery: RecoverySection;
  sleep: SleepSection;
  strain: StrainSection;
  workouts: WorkoutsSection | null;
  journal: JournalSection | null;
  trends: TrendsSection;
  insights: Insight[];
};

export type ShareCreateRequest = { report: WhoopReport };
export type ShareCreateResponse = {
  id: string;
  url: string;
  expires_at: string; // ISO datetime
};

export type ApiErrorBody = {
  code: string;
  file?: string;
  limit_mb?: number;
  missing_cols?: string[];
  extra_cols?: string[];
  error_id?: string;
  [key: string]: unknown;
};
