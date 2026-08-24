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
    benchmark_mean: float | None = None
    benchmark_median: float | None = None
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
