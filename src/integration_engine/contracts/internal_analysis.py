from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .analysis import AnalyzeResponse, CompetitiveContext, PlayerReference


class AnalyzePlayerRequest(BaseModel):
    request_id: str | None = None
    source: Literal["player", "partner", "internal"] = "partner"
    player: PlayerReference
    match_count: int = Field(default=20, ge=1, le=100)
    learn: bool = True


class AnalyzeRawMatchRequest(BaseModel):
    request_id: str | None = None
    source: Literal["player", "partner", "challenger", "internal"] = "partner"
    puuid: str
    match_data: dict[str, Any]
    learn: bool = False

    @model_validator(mode="after")
    def validate_raw_match(self) -> "AnalyzeRawMatchRequest":
        if not self.puuid.strip():
            raise ValueError("puuid não pode ser vazio.")

        if not self.match_data:
            raise ValueError("match_data não pode ser vazio.")

        return self


class CacheStatistics(BaseModel):
    match_ids_received: int
    cached_matches_used: int
    new_matches_downloaded: int
    transformed_matches: int
    failed_matches: int


class LearningStatistics(BaseModel):
    enabled: bool
    inserted: int = 0
    reused: int = 0
    observations_written: int = 0


class IntegratedAnalysisResponse(BaseModel):
    analysis: AnalyzeResponse
    cache: CacheStatistics
    learning: LearningStatistics
    player_puuid: str
    matches_analyzed: int
    patch: str | None = None
    set_number: int | None = None
    competitive_context: CompetitiveContext | None = None
