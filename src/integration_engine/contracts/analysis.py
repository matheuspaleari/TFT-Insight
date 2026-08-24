from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .common import (
    ApiMeta,
    EvidenceItem,
    LimitationItem,
)


class PlayerReference(BaseModel):
    puuid: str | None = None
    game_name: str | None = None
    tag_line: str | None = None
    region: str = "BR1"

    @model_validator(mode="after")
    def validate_reference(self) -> "PlayerReference":
        has_puuid = bool(self.puuid)
        has_riot_id = bool(
            self.game_name and self.tag_line
        )

        if not has_puuid and not has_riot_id:
            raise ValueError(
                "Informe puuid ou game_name + tag_line."
            )

        return self


class AnalysisSignals(BaseModel):
    economy_score: float = Field(
        ge=0.0,
        le=100.0,
    )
    itemization_score: float = Field(
        ge=0.0,
        le=100.0,
    )
    tempo_score: float = Field(
        ge=0.0,
        le=100.0,
    )
    contest_score: float = Field(
        ge=0.0,
        le=100.0,
        description=(
            "Score estratégico de contestação: "
            "100 representa baixa contestação."
        ),
    )
    flex_score: float = Field(
        ge=0.0,
        le=100.0,
    )
    benchmark_score: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
    )
    sample_size: int = Field(
        default=20,
        ge=1,
    )

    carry_contested: bool = False
    opponents_on_carry: int = Field(
        default=0,
        ge=0,
    )
    average_placement: float | None = Field(
        default=None,
        ge=1.0,
        le=8.0,
    )


class AnalyzeRequest(BaseModel):
    request_id: str | None = None
    source: Literal[
        "partner",
        "player",
        "challenger",
        "internal",
    ] = "partner"

    player: PlayerReference | None = None
    patch: str | None = None
    set_number: int | None = None
    signals: AnalysisSignals


class PredictionResult(BaseModel):
    top1_probability: float
    top4_probability: float
    bot4_probability: float
    expected_placement: float
    risk: Literal[
        "Baixo",
        "Médio",
        "Alto",
        "Muito alto",
    ]
    confidence: float


class FeatureContribution(BaseModel):
    feature: str
    score: float
    weight: float
    contribution: float
    direction: Literal[
        "positive",
        "negative",
        "neutral",
    ]


class RecommendationItem(BaseModel):
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


class CoachResult(BaseModel):
    headline: str
    summary: str
    pregame_attention: str
    win_condition: str



class SpectrumMetricItem(BaseModel):
    metric: str
    score: float = Field(ge=0.0, le=100.0)
    player_value: float
    benchmark_value: float
    classification: Literal[
        "STRENGTH",
        "NEUTRAL",
        "ATTENTION",
    ]


class CompetitiveSpectrum(BaseModel):
    available: bool
    benchmark_id: str
    group_label: str
    current_rank: str
    spectrum_position: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )
    spectrum_percentile: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )
    spectrum_band: str | None = None
    spectrum_band_id: str | None = None
    population_size: int = Field(default=0, ge=0)
    strengths: tuple[str, ...] = ()
    neutral_areas: tuple[str, ...] = ()
    attention_areas: tuple[str, ...] = ()
    performance_profile: tuple[SpectrumMetricItem, ...] = ()
    limitation: str | None = None


class CompetitiveContext(BaseModel):
    queue_type: str = "RANKED_TFT"
    ranked: bool
    current_rank: str
    tier: str | None = None
    division: str | None = None
    league_points: int | None = None
    current_stage: str
    target_stage: str
    profile_id: str
    benchmark_id: str
    spectrum: CompetitiveSpectrum | None = None


class AnalyzeResponse(BaseModel):
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

    # Contexto competitivo anexado pelo fluxo /v1/analyze/player.
    # Campos de conveniência mantêm compatibilidade com a UI atual.
    competitive_context: CompetitiveContext | None = None
    current_rank: str | None = None
    current_stage: str | None = None
    target_stage: str | None = None
    profile_id: str | None = None
    benchmark_id: str | None = None
