from __future__ import annotations
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.contest_intelligence import ContestIntelligenceEngine, ContestPlayerPresenter
from src.decision_engine import ContestHistoryAnalyzer
from src.integration_engine.api.dependencies import require_api_key
from src.integration_engine.services.cached_match_service import CachedMatchService

PROJECT_ROOT = Path(__file__).resolve().parents[4]

class ContestPlayerRequest(BaseModel):
    game_name: str = Field(min_length=1)
    tag_line: str = Field(min_length=1)

class ContestIntelligenceRequest(BaseModel):
    player: ContestPlayerRequest
    match_count: int = Field(default=30, ge=10, le=50)

router = APIRouter(
    prefix="/v1/contest-intelligence",
    tags=["contest-intelligence"],
)

@router.post("/player/history")
def player_contest_intelligence(
    request: ContestIntelligenceRequest,
    _: str = Depends(require_api_key),
) -> dict:
    try:
        loader = CachedMatchService(project_root=PROJECT_ROOT)
        puuid = loader.resolve_puuid(
            puuid=None,
            game_name=request.player.game_name,
            tag_line=request.player.tag_line,
        )
        candidate_count = min(
            max(request.match_count * 2, request.match_count + 10),
            100,
        )
        load_result = loader.load_player_matches_target(
            puuid=puuid,
            target_count=request.match_count,
            candidate_count=candidate_count,
        )
        matches = list(load_result.matches)

        if len(matches) < 3:
            raise ValueError(
                "Não há partidas válidas suficientes para analisar contestação."
            )

        history = ContestHistoryAnalyzer.analyze(matches)
        intelligence = ContestIntelligenceEngine.build(history)
        payload = ContestPlayerPresenter.build(intelligence)

        payload["player"] = {
            "game_name": request.player.game_name,
            "tag_line": request.player.tag_line,
        }
        payload["collection"] = {
            "requested_matches": request.match_count,
            "valid_matches": len(matches),
            "candidate_ids_received": load_result.match_ids_received,
            "cached_matches_used": load_result.cached_matches_used,
            "new_matches_downloaded": load_result.new_matches_downloaded,
            "failed_matches": load_result.failed_matches,
            "candidate_ids_considered": load_result.candidate_ids_considered,
            "load_elapsed_seconds": load_result.elapsed_seconds,
            "cache_hit_rate": load_result.cache_hit_rate,
            "stopped_after_target": load_result.stopped_after_target,
        }
        return payload

    except (ValueError, RuntimeError, KeyError, AttributeError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
