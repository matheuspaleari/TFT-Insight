from pydantic import BaseModel, Field

from .analysis import PlayerReference


class BenchmarkComparePlayerRequest(BaseModel):
    player: PlayerReference
    match_count: int = Field(
        default=20,
        ge=5,
        le=100,
    )


class BenchmarkMetricDistribution(BaseModel):
    label: str
    mean: float
    median: float
    minimum: float
    maximum: float
    q25: float
    q75: float


class BenchmarkPlayerItem(BaseModel):
    puuid: str
    game_name: str
    tag_line: str = ""
    matches_played: int
    average_placement: float
    top4_rate: float
    win_rate: float
    average_level: float
    average_damage_to_players: float


class BenchmarkOverviewResponse(BaseModel):
    benchmark_id: str
    name: str
    players_analyzed: int
    matches_analyzed: int
    metrics: dict[
        str,
        BenchmarkMetricDistribution,
    ]
    players: list[
        BenchmarkPlayerItem
    ] = Field(
        default_factory=list
    )
    catalog_source: str


class BenchmarkComparisonItem(BaseModel):
    metric: str
    label: str
    player_value: float
    challenger_mean: float
    challenger_median: float
    delta: float
    performance_delta: float
    percentile: float | None = None
    assessment: str


class BenchmarkRadarItem(BaseModel):
    metric: str
    player: float
    challenger_reference: float


class BenchmarkComparedPlayer(BaseModel):
    puuid: str
    matches_analyzed: int
    metrics: dict[
        str,
        float | None,
    ]


class BenchmarkCompositionCoachContext(BaseModel):
    matches_analyzed: int
    unique_compositions: int
    diversity_rate: float
    repetition_rate: float
    forces_composition: bool
    flexibility_label: str = "indeterminado"
    flexibility_interpretation: str = ""

    most_used_composition_key: str
    most_used_carry_character_id: str = ""
    most_used_matches: int
    most_used_usage_rate: float
    most_used_average_placement: float
    most_used_top4_rate: float
    most_used_win_rate: float
    most_used_average_contest_score: float | None = None

    best_composition_key: str
    best_carry_character_id: str = ""
    best_average_placement: float
    best_top4_rate: float

    recommendation_label: str = ""
    recommendation_explanation: str = ""


class BenchmarkContestCoachContext(BaseModel):
    matches_analyzed: int
    average_score: float
    high_contest_rate: float
    carry_contest_rate: float
    placement_impact: float | None = None
    placement_impact_label: str = "indeterminado"
    placement_impact_interpretation: str = ""

    most_contested_unit_id: str = ""
    most_contested_trait_name: str = ""

    latest_carry_character_id: str = ""
    latest_carry_contested: bool
    latest_opponents_contesting_carry: int
    latest_contested_unit_ids: list[str] = Field(
        default_factory=list
    )
    latest_contested_trait_names: list[str] = Field(
        default_factory=list
    )

    action: str
    confidence: float
    explanation: str


class BenchmarkEconomyCoachContext(BaseModel):
    matches_analyzed: int
    score: float
    label: str
    interpretation: str = ""
    average_level: float
    average_gold_left: float
    average_last_round: float
    level_8_rate: float
    level_9_rate: float
    low_level_late_rate: float

    action: str
    confidence: float
    explanation: str


class BenchmarkCoachContext(BaseModel):
    composition: BenchmarkCompositionCoachContext
    contest: BenchmarkContestCoachContext
    economy: BenchmarkEconomyCoachContext


class BenchmarkTrainingMission(BaseModel):
    skill_id: str
    skill_name: str
    task_id: str
    task_difficulty: str = "FOUNDATION"
    title: str
    objective: str
    checklist: list[str]
    games_completed: int
    games_target: int
    remaining_games: int
    progress_percentage: float
    is_completed: bool


class BenchmarkTrainingEvaluationMetric(BaseModel):
    metric_id: str
    before: float | None = None
    after: float | None = None
    delta: float | None = None
    relative_change: float | None = None
    direction: str


class BenchmarkTrainingEvaluation(BaseModel):
    result: str
    confidence: str
    confidence_score: float
    positive_metrics: int
    stable_metrics: int
    negative_metrics: int
    before_sample_size: int
    after_sample_size: int
    reason: str
    caveat: str
    metrics: list[BenchmarkTrainingEvaluationMetric] = Field(
        default_factory=list
    )


class BenchmarkTrainingHistoryItem(BaseModel):
    skill_id: str
    skill_name: str
    task_id: str
    title: str
    games_completed: int
    games_target: int
    archived_at: str
    status: str = "completed"
    evaluation: BenchmarkTrainingEvaluation | None = None


class BenchmarkLearningSkillState(BaseModel):
    cycles_total: int
    evaluated_cycles: int
    conclusive_cycles: int
    trend: str
    trend_confidence: str
    latest_result: str | None = None
    anti_loop_action: str
    task_progression: str
    consecutive_skill_cycles: int
    last_task_id: str | None = None
    last_task_title: str | None = None
    current_task_id: str | None = None
    current_difficulty: str | None = None


class BenchmarkLearningState(BaseModel):
    version: int = 1
    current_skill_id: str | None = None
    skills: dict[
        str,
        BenchmarkLearningSkillState,
    ] = Field(
        default_factory=dict
    )
    last_decision: dict | None = None


class BenchmarkTrainingContext(BaseModel):
    mission: BenchmarkTrainingMission
    coach_message: str
    cycle_stage: str
    cycle_stage_label: str
    cycle_message: str
    current_priority_skill_id: str | None = None
    current_priority_name: str | None = None
    history: list[BenchmarkTrainingHistoryItem] = Field(
        default_factory=list
    )
    learning_state: BenchmarkLearningState | None = None


class BenchmarkAdaptiveStrategy(BaseModel):
    priority_skill_id: str
    strategy: str
    confidence: str
    current_level: str
    current_score: float | None = None
    training_trend: str
    current_difficulty: str | None = None
    current_task_id: str | None = None
    task_effectiveness: str
    anti_loop_action: str
    rationale: str
    safeguards: list[str] = Field(
        default_factory=list
    )


class BenchmarkCoachExplanation(BaseModel):
    title: str
    summary: str
    next_step: str
    evidence: list[str] = Field(
        default_factory=list
    )
    limitations: list[str] = Field(
        default_factory=list
    )
    source: str = "deterministic"


class BenchmarkAdaptiveCoach(BaseModel):
    strategy: BenchmarkAdaptiveStrategy
    explanation: BenchmarkCoachExplanation
    profile: dict
    evolution: list[dict] = Field(
        default_factory=list
    )
    cross_skill_insights: list[dict] = Field(
        default_factory=list
    )
    training_effectiveness: list[dict] = Field(
        default_factory=list
    )


class BenchmarkProgressDashboard(BaseModel):
    timelines: dict[str, list[dict]] = Field(
        default_factory=dict
    )
    overall_development: dict = Field(
        default_factory=dict
    )
    insights: list[dict] = Field(
        default_factory=list
    )
    milestones: list[dict] = Field(
        default_factory=list
    )
    snapshot_count: int = 0


class BenchmarkProgressAwareCoach(BaseModel):
    context: dict = Field(default_factory=dict)
    strategy: dict = Field(default_factory=dict)
    adaptation: dict = Field(default_factory=dict)
    explanation: dict = Field(default_factory=dict)


class BenchmarkCompareResponse(BaseModel):
    benchmark: BenchmarkOverviewResponse
    player: BenchmarkComparedPlayer
    overall_percentile: float | None = None
    classification: str
    comparisons: list[
        BenchmarkComparisonItem
    ]
    radar: list[
        BenchmarkRadarItem
    ]
    coach_context: BenchmarkCoachContext | None = None
    training: BenchmarkTrainingContext | None = None
    adaptive_coach: BenchmarkAdaptiveCoach | None = None
    progress: BenchmarkProgressDashboard | None = None
    progress_aware_coach: BenchmarkProgressAwareCoach | None = None
    coach_fusion: dict = Field(default_factory=dict)
