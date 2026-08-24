from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from src.integration_engine.api.dependencies import (
    require_api_key,
)
from src.integration_engine.contracts import (
    AnalyzePlayerRequest,
    AnalyzeRawMatchRequest,
    CacheStatistics,
    CompetitiveContext,
    IntegratedAnalysisResponse,
)
from src.integration_engine.services.cached_match_service import (
    CachedMatchService,
)
from src.integration_engine.services.internal_analysis_pipeline import (
    InternalAnalysisPipeline,
)
from src.benchmark import BenchmarkContextBuilder, CompetitiveSpectrumEngine
from src.rank_history import RankObservationService
from src.riot_client import RiotClient
from src.transformers.match_transformer import (
    MatchTransformer,
)


PROJECT_ROOT = Path(__file__).resolve().parents[4]

router = APIRouter(
    prefix="/v1/analyze",
    tags=["integrated-analysis"],
)



def _rank_display(
    ranked_entry: dict | None,
) -> str:
    if not isinstance(ranked_entry, dict):
        return "Não ranqueado"

    tier = str(
        ranked_entry.get("tier", "")
    ).strip().upper()
    division = str(
        ranked_entry.get("rank", "")
    ).strip().upper()
    lp = ranked_entry.get("leaguePoints")

    if not tier:
        return "Não ranqueado"

    value = tier
    if division:
        value += f" {division}"
    if isinstance(lp, int):
        value += f" · {lp} LP"

    return value


def _competitive_context(
    *,
    riot_client: RiotClient,
    puuid: str,
) -> tuple[CompetitiveContext, dict | None]:
    ranked_entry = riot_client.get_ranked_tft_entry(
        puuid=puuid,
        queue_type="RANKED_TFT",
    )

    tier = None
    division = None
    league_points = None

    if isinstance(ranked_entry, dict):
        raw_tier = ranked_entry.get("tier")
        raw_division = ranked_entry.get("rank")
        raw_lp = ranked_entry.get("leaguePoints")

        if isinstance(raw_tier, str) and raw_tier.strip():
            tier = raw_tier.strip().upper()

        if isinstance(raw_division, str) and raw_division.strip():
            division = raw_division.strip().upper()

        if isinstance(raw_lp, int):
            league_points = raw_lp

    benchmark_rank = tier or "IRON"

    benchmark_context = BenchmarkContextBuilder.build(
        current_rank=benchmark_rank,
    )

    return (
        CompetitiveContext(
            queue_type="RANKED_TFT",
            ranked=tier is not None,
            current_rank=_rank_display(ranked_entry),
            tier=tier,
            division=division,
            league_points=league_points,
            current_stage=benchmark_context.group.display_name,
            target_stage=benchmark_context.group.target_stage,
            profile_id=benchmark_context.profile.id,
            benchmark_id=benchmark_context.benchmark_id,
        ),
        ranked_entry,
    )


@router.post(
    "/player",
    response_model=IntegratedAnalysisResponse,
)
def analyze_player(
    request: AnalyzePlayerRequest,
    _: str = Depends(require_api_key),
) -> IntegratedAnalysisResponse:
    try:
        loader = CachedMatchService(
            project_root=PROJECT_ROOT
        )

        puuid = loader.resolve_puuid(
            puuid=request.player.puuid,
            game_name=request.player.game_name,
            tag_line=request.player.tag_line,
        )

        riot_client = RiotClient()

        competitive_context, ranked_entry = (
            _competitive_context(
                riot_client=riot_client,
                puuid=puuid,
            )
        )

        result = loader.load_player_matches(
            puuid=puuid,
            count=request.match_count,
        )

        spectrum_result = CompetitiveSpectrumEngine(
            benchmark_directory=(
                PROJECT_ROOT / "data" / "benchmark"
            )
        ).analyze(
            benchmark_id=competitive_context.benchmark_id,
            group_label=competitive_context.current_stage,
            tier=competitive_context.tier,
            division=competitive_context.division,
            league_points=competitive_context.league_points,
            current_rank=competitive_context.current_rank,
        )

        competitive_context = competitive_context.model_copy(
            update={
                "spectrum": spectrum_result.to_dict(),
            }
        )

        # O histórico de elo precisa de uma janela maior que a análise
        # para conseguir localizar o último ponto de corte.
        rank_match_ids = riot_client.get_match_ids(
            puuid=puuid,
            count=RankObservationService.DEFAULT_SCAN_LIMIT,
        )

        if (
            request.player.game_name
            and request.player.tag_line
        ):
            RankObservationService(
                riot_client=riot_client,
            ).record_resolved(
                puuid=puuid,
                game_name=request.player.game_name,
                tag_line=request.player.tag_line,
                ranked_entry=ranked_entry,
                current_match_ids=rank_match_ids,
                scan_limit=(
                    RankObservationService.DEFAULT_SCAN_LIMIT
                ),
            )

        pipeline = InternalAnalysisPipeline(
            project_root=PROJECT_ROOT
        )

        return pipeline.analyze_matches(
            matches=result.matches,
            payloads=result.payloads,
            player_puuid=puuid,
            source=request.source,
            request_id=request.request_id,
            learn=request.learn,
            cache_statistics=CacheStatistics(
                match_ids_received=(
                    result.match_ids_received
                ),
                cached_matches_used=(
                    result.cached_matches_used
                ),
                new_matches_downloaded=(
                    result.new_matches_downloaded
                ),
                transformed_matches=len(
                    result.matches
                ),
                failed_matches=result.failed_matches,
            ),
            competitive_context=competitive_context,
        )

    except (ValueError, RuntimeError, KeyError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error


@router.post(
    "/match",
    response_model=IntegratedAnalysisResponse,
)
def analyze_raw_match(
    request: AnalyzeRawMatchRequest,
    _: str = Depends(require_api_key),
) -> IntegratedAnalysisResponse:
    try:
        match = MatchTransformer.transform(
            match_data=request.match_data,
            puuid=request.puuid,
        )

        pipeline = InternalAnalysisPipeline(
            project_root=PROJECT_ROOT
        )

        return pipeline.analyze_matches(
            matches=[match],
            payloads=[request.match_data],
            player_puuid=request.puuid,
            source=request.source,
            request_id=request.request_id,
            learn=request.learn,
            cache_statistics=CacheStatistics(
                match_ids_received=1,
                cached_matches_used=0,
                new_matches_downloaded=0,
                transformed_matches=1,
                failed_matches=0,
            ),
        )

    except (ValueError, RuntimeError, KeyError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
