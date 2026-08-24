from __future__ import annotations

from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from pydantic import BaseModel, Field

from src.composition_intelligence_v2 import (
    CompositionIntelligenceV2,
)
from src.composition_intelligence_v2.services.composition_player_presenter import (
    CompositionPlayerPresenter,
)
from src.decision_engine import (
    CompositionHistoryAnalyzer,
    ContestHistoryAnalyzer,
)
from src.integration_engine.api.dependencies import (
    require_api_key,
)
from src.integration_engine.services.cached_match_service import (
    CachedMatchService,
)
from src.integration_engine.services.item_classification_provider import (
    ItemClassificationProvider,
)


PROJECT_ROOT = Path(
    __file__
).resolve().parents[4]


class CompositionPlayerRequest(BaseModel):
    game_name: str = Field(min_length=1)
    tag_line: str = Field(min_length=1)


class CompositionIntelligenceRequest(BaseModel):
    player: CompositionPlayerRequest
    match_count: int = Field(
        default=30,
        ge=10,
        le=50,
    )


router = APIRouter(
    prefix="/v1/composition-intelligence",
    tags=["composition-intelligence"],
)


@router.post(
    "/player/history",
)
def player_composition_intelligence(
    request: CompositionIntelligenceRequest,
    _: str = Depends(require_api_key),
) -> dict:
    try:
        loader = CachedMatchService(
            project_root=PROJECT_ROOT
        )

        puuid = loader.resolve_puuid(
            puuid=None,
            game_name=request.player.game_name,
            tag_line=request.player.tag_line,
        )

        # Busca candidatos extras porque o MatchTransformer pode
        # corretamente rejeitar partidas incompatíveis com o modelo
        # analítico atual (ex.: PUUID duplicado).
        candidate_count = min(
            max(
                request.match_count * 2,
                request.match_count + 10,
            ),
            100,
        )

        load_result = loader.load_player_matches_target(
            puuid=puuid,
            target_count=request.match_count,
            candidate_count=candidate_count,
        )

        matches = list(
            load_result.matches
        )

        if len(matches) < 3:
            raise ValueError(
                "Não há partidas válidas suficientes para "
                "analisar composições."
            )

        classifications = (
            ItemClassificationProvider(
                project_root=PROJECT_ROOT
            ).get()
        )

        contest_history = (
            ContestHistoryAnalyzer.analyze(
                matches
            )
        )

        history = (
            CompositionHistoryAnalyzer.analyze(
                matches,
                contest_history=contest_history,
                item_classifications=classifications,
            )
        )

        intelligence = (
            CompositionIntelligenceV2.build(
                history
            )
        )

        payload = (
            CompositionPlayerPresenter.build(
                intelligence
            )
        )

        payload["player"] = {
            "game_name": request.player.game_name,
            "tag_line": request.player.tag_line,
        }

        payload["collection"] = {
            "requested_matches": request.match_count,
            "valid_matches": len(matches),
            "candidate_ids_received": (
                load_result.match_ids_received
            ),
            "cached_matches_used": (
                load_result.cached_matches_used
            ),
            "new_matches_downloaded": (
                load_result.new_matches_downloaded
            ),
            "failed_matches": (
                load_result.failed_matches
            ),
            "candidate_ids_considered": (
                load_result.candidate_ids_considered
            ),
            "load_elapsed_seconds": (
                load_result.elapsed_seconds
            ),
            "cache_hit_rate": (
                load_result.cache_hit_rate
            ),
            "stopped_after_target": (
                load_result.stopped_after_target
            ),
        }

        return payload

    except (
        ValueError,
        RuntimeError,
        KeyError,
        AttributeError,
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(error),
        ) from error
