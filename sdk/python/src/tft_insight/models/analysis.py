from typing import Literal

from pydantic import Field

from .common import (
    ApiMeta,
    EvidenceItem,
    LimitationItem,
    SDKModel,
)


class PredictionResult(SDKModel):
    top1_probability: float
    top4_probability: float
    bot4_probability: float
    expected_placement: float
    risk: str
    confidence: float


class FeatureContribution(SDKModel):
    feature: str
    score: float
    weight: float
    contribution: float
    direction: Literal[
        "positive",
        "negative",
        "neutral",
    ]


class RecommendationItem(SDKModel):
    priority: Literal[
        "critical",
        "high",
        "medium",
        "low",
    ]
    category: str
    title: str
    action: str
    confidence: float


class CoachResult(SDKModel):
    headline: str
    summary: str
    pregame_attention: str
    win_condition: str


class AnalyzeResponse(SDKModel):
    meta: ApiMeta
    overall_score: float
    classification: str
    prediction: PredictionResult
    feature_importance: tuple[
        FeatureContribution,
        ...,
    ]
    recommendations: tuple[
        RecommendationItem,
        ...,
    ]
    coach: CoachResult
    evidence: tuple[EvidenceItem, ...]
    limitations: tuple[LimitationItem, ...]


class CacheStatistics(SDKModel):
    match_ids_received: int
    cached_matches_used: int
    new_matches_downloaded: int
    transformed_matches: int
    failed_matches: int


class LearningStatistics(SDKModel):
    enabled: bool
    inserted: int = 0
    reused: int = 0
    observations_written: int = 0


class IntegratedAnalysisResponse(SDKModel):
    analysis: AnalyzeResponse
    cache: CacheStatistics
    learning: LearningStatistics
    player_puuid: str
    matches_analyzed: int
    patch: str | None = None
    set_number: int | None = None


class AnalysisSignals(SDKModel):
    economy_score: float = Field(ge=0, le=100)
    itemization_score: float = Field(ge=0, le=100)
    tempo_score: float = Field(ge=0, le=100)
    contest_score: float = Field(ge=0, le=100)
    flex_score: float = Field(ge=0, le=100)
    benchmark_score: float = Field(default=50, ge=0, le=100)
    sample_size: int = Field(default=20, ge=1)
    carry_contested: bool = False
    opponents_on_carry: int = Field(default=0, ge=0)
    average_placement: float | None = Field(
        default=None,
        ge=1,
        le=8,
    )
