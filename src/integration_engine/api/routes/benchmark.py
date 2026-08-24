from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.benchmark_intelligence import BenchmarkIntelligenceService
from src.coach_intelligence.services.adaptive_coach_intelligence_service import (
    AdaptiveCoachIntelligenceService,
)
from src.coach.services.coach_pipeline_service import CoachPipelineService
from src.integration_engine.api.dependencies import require_api_key
from src.integration_engine.contracts import (
    BenchmarkComparePlayerRequest,
    BenchmarkCompareResponse,
    BenchmarkOverviewResponse,
)
from src.integration_engine.services.benchmark_coach_context_builder import BenchmarkCoachContextBuilder
from src.integration_engine.services.cached_match_service import CachedMatchService
from src.services import PlayerAnalysisService
from src.learning import SkillMappingService
from src.progress_intelligence.services.progress_history_service import (
    ProgressHistoryService,
)
from src.progress_intelligence.services.progress_intelligence_service import (
    ProgressIntelligenceService,
)
from src.progress_intelligence.services.progress_milestone_service import (
    ProgressMilestoneService,
)
from src.progress_intelligence.services.progress_snapshot_service import (
    ProgressSnapshotService,
)
from src.progress_aware_coach import ProgressAwareCoachService
from src.storage import PlayerRepository
from src.training.services.training_cycle_evaluation_service import (
    TrainingCycleEvaluationService,
)
from src.training.services.pedagogical_memory_service import (
    PedagogicalMemoryService,
)


PROJECT_ROOT = Path(__file__).resolve().parents[4]

router = APIRouter(
    prefix="/v1/benchmark",
    tags=["benchmark-intelligence"],
)



_SKILL_LABELS = {
    "leveling": "Leveling",
    "consistency": "Consistência",
    "board_pressure": "Pressão de tabuleiro",
    "economy": "Economia",
    "composition_flexibility": "Flexibilidade de composição",
    "lobby_reading": "Leitura de lobby",
}


def _skill_label(
    skill_id: str,
) -> str:
    return _SKILL_LABELS.get(
        skill_id,
        skill_id.replace(
            "_",
            " ",
        ).title(),
    )


def _training_history_payload(
    *,
    cycles: list[dict],
    current_completed_mission_id: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    Converte o histórico persistido em um payload seguro para a UI.

    Não expõe baseline, match_ids, mission_id ou outros detalhes internos.
    O ciclo que acabou de chegar a 5/5 não é duplicado na UI enquanto
    ainda está sendo mostrado como a missão atual.
    """

    items: list[dict] = []

    for cycle in cycles:
        cycle_id = str(
            cycle.get(
                "cycle_id",
                "",
            )
        )

        if (
            current_completed_mission_id
            and cycle_id
            == current_completed_mission_id
        ):
            continue

        mission = cycle.get(
            "mission",
            {},
        )

        if not isinstance(
            mission,
            dict,
        ):
            continue

        task = mission.get(
            "task",
            {},
        )

        if not isinstance(
            task,
            dict,
        ):
            task = {}

        skill_id = str(
            task.get(
                "skill_id",
                "",
            )
            or ""
        )

        title = str(
            task.get(
                "title",
                "",
            )
            or mission.get(
                "title",
                "",
            )
            or "Ciclo de treinamento"
        )

        evaluation = cycle.get(
            "evaluation",
            {},
        )

        if not isinstance(
            evaluation,
            dict,
        ):
            evaluation = {}

        public_evaluation = None

        if evaluation:
            metric_items = []

            for metric in evaluation.get(
                "metric_evaluations",
                [],
            ):
                if not isinstance(
                    metric,
                    dict,
                ):
                    continue

                metric_items.append(
                    {
                        "metric_id": str(
                            metric.get(
                                "metric_id",
                                "",
                            )
                        ),
                        "before": metric.get(
                            "before"
                        ),
                        "after": metric.get(
                            "after"
                        ),
                        "delta": metric.get(
                            "delta"
                        ),
                        "relative_change": metric.get(
                            "relative_change"
                        ),
                        "direction": str(
                            metric.get(
                                "direction",
                                "",
                            )
                        ),
                    }
                )

            public_evaluation = {
                "result": str(
                    evaluation.get(
                        "result",
                        "",
                    )
                ),
                "confidence": str(
                    evaluation.get(
                        "confidence",
                        "",
                    )
                ),
                "confidence_score": float(
                    evaluation.get(
                        "confidence_score",
                        0.0,
                    )
                    or 0.0
                ),
                "positive_metrics": int(
                    evaluation.get(
                        "positive_metrics",
                        0,
                    )
                    or 0
                ),
                "stable_metrics": int(
                    evaluation.get(
                        "stable_metrics",
                        0,
                    )
                    or 0
                ),
                "negative_metrics": int(
                    evaluation.get(
                        "negative_metrics",
                        0,
                    )
                    or 0
                ),
                "before_sample_size": int(
                    evaluation.get(
                        "before_sample_size",
                        0,
                    )
                    or 0
                ),
                "after_sample_size": int(
                    evaluation.get(
                        "after_sample_size",
                        0,
                    )
                    or 0
                ),
                "reason": str(
                    evaluation.get(
                        "reason",
                        "",
                    )
                ),
                "caveat": str(
                    evaluation.get(
                        "caveat",
                        "",
                    )
                ),
                "metrics": metric_items,
            }

        items.append(
            {
                "skill_id": skill_id,
                "skill_name": _skill_label(
                    skill_id
                ),
                "task_id": str(
                    task.get(
                        "id",
                        "",
                    )
                    or ""
                ),
                "title": title,
                "games_completed": int(
                    mission.get(
                        "games_completed",
                        0,
                    )
                    or 0
                ),
                "games_target": int(
                    mission.get(
                        "games_target",
                        0,
                    )
                    or 0
                ),
                "archived_at": str(
                    cycle.get(
                        "archived_at",
                        "",
                    )
                    or ""
                ),
                "status": str(
                    cycle.get(
                        "status",
                        "completed",
                    )
                    or "completed"
                ),
                "evaluation": public_evaluation,
            }
        )

        if len(items) >= limit:
            break

    return items


def _training_payload(
    pipeline,
    *,
    history: list[dict] | None = None,
    learning_state: dict | None = None,
) -> dict:
    mission = pipeline.mission
    training_plan = pipeline.training_plan

    priority_id = None
    priority_name = None
    if training_plan is not None:
        priority_id = training_plan.primary_skill_id
        priority_name = training_plan.primary_skill_label

    return {
        "mission": {
            "skill_id": mission.skill_id,
            "skill_name": priority_name if priority_id == mission.skill_id else mission.skill_id,
            "task_id": mission.task.id,
            "task_difficulty": str(
                getattr(
                    mission.task,
                    "difficulty",
                    "FOUNDATION",
                )
            ),
            "title": mission.title,
            "objective": mission.task.habit,
            "checklist": list(mission.task.checklist),
            "games_completed": mission.games_completed,
            "games_target": mission.games_target,
            "remaining_games": mission.remaining_games,
            "progress_percentage": mission.progress_percentage,
            "is_completed": mission.is_completed,
        },
        "coach_message": pipeline.coach_message,
        "cycle_stage": pipeline.cycle_stage,
        "cycle_stage_label": pipeline.cycle_stage_label,
        "cycle_message": pipeline.cycle_message,
        "current_priority_skill_id": priority_id,
        "current_priority_name": priority_name,
        "history": history or [],
        "learning_state": learning_state,
    }


@router.get("/challenger", response_model=BenchmarkOverviewResponse)
def challenger_overview(
    include_players: bool = Query(default=True),
    _: str = Depends(require_api_key),
) -> BenchmarkOverviewResponse:
    try:
        service = BenchmarkIntelligenceService(project_root=PROJECT_ROOT)
        return BenchmarkOverviewResponse.model_validate(
            service.overview(include_players=include_players)
        )
    except (ValueError, RuntimeError, KeyError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error


@router.post("/challenger/compare/player", response_model=BenchmarkCompareResponse)
def compare_player(
    request: BenchmarkComparePlayerRequest,
    _: str = Depends(require_api_key),
) -> BenchmarkCompareResponse:
    return compare_player_to_benchmark(
        benchmark_id="challenger_br",
        request=request,
        _=_,
    )


@router.get("/{benchmark_id}", response_model=BenchmarkOverviewResponse)
def benchmark_overview(
    benchmark_id: str,
    include_players: bool = Query(default=True),
    _: str = Depends(require_api_key),
) -> BenchmarkOverviewResponse:
    try:
        service = BenchmarkIntelligenceService(project_root=PROJECT_ROOT)
        return BenchmarkOverviewResponse.model_validate(
            service.overview_for(
                benchmark_id=benchmark_id,
                include_players=include_players,
            )
        )
    except (ValueError, RuntimeError, KeyError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error


@router.post("/{benchmark_id}/compare/player", response_model=BenchmarkCompareResponse)
def compare_player_to_benchmark(
    benchmark_id: str,
    request: BenchmarkComparePlayerRequest,
    _: str = Depends(require_api_key),
) -> BenchmarkCompareResponse:
    try:
        loader = CachedMatchService(project_root=PROJECT_ROOT)
        puuid = loader.resolve_puuid(
            puuid=request.player.puuid,
            game_name=request.player.game_name,
            tag_line=request.player.tag_line,
        )
        result = loader.load_player_matches(
            puuid=puuid,
            count=request.match_count,
        )

        service = BenchmarkIntelligenceService(project_root=PROJECT_ROOT)
        comparison_data = service.compare_matches_to(
            benchmark_id=benchmark_id,
            matches=result.matches,
            player_puuid=puuid,
        )

        coach_context = BenchmarkCoachContextBuilder.build(
            project_root=PROJECT_ROOT,
            matches=result.matches,
        )
        comparison_data["coach_context"] = coach_context

        # Reaproveita PlayerAnalysisService com cache para obter a Performance
        # oficial sem duplicar o pipeline de coaching.
        analysis = PlayerAnalysisService().analyze(
            game_name=request.player.game_name or "",
            tag_line=request.player.tag_line or "",
            benchmark_id=benchmark_id,
            match_count=request.match_count,
            use_cache=True,
        )

        pipeline = CoachPipelineService().run(
            puuid=puuid,
            performance=analysis.performance,
            coach_context=coach_context,
            current_match_ids=tuple(analysis.match_ids),
            mission_games_target=5,
            competitive_spectrum=(
                analysis.competitive_spectrum
                if isinstance(
                    analysis.competitive_spectrum,
                    dict,
                )
                else None
            ),
        )

        comparison_data["coach_fusion"] = (
            pipeline.context_fusion
        )

        training_repository = PlayerRepository()

        archived_cycles = (
            training_repository.list_training_cycles(
                puuid=puuid
            )
        )

        evaluation_service = (
            TrainingCycleEvaluationService(
                player_repository=(
                    training_repository
                ),
                cached_match_service=(
                    CachedMatchService(
                        project_root=PROJECT_ROOT
                    )
                ),
            )
        )

        archived_cycles = (
            evaluation_service.evaluate_pending_cycles(
                puuid=puuid,
                cycles=archived_cycles,
                limit=10,
            )
        )

        current_completed_mission_id = (
            pipeline.mission.mission_id
            if pipeline.mission.is_completed
            else None
        )

        training_history = (
            _training_history_payload(
                cycles=archived_cycles,
                current_completed_mission_id=(
                    current_completed_mission_id
                ),
            )
        )

        memory_service = PedagogicalMemoryService(
            player_repository=(
                training_repository
            )
        )

        pedagogical_memory = (
            memory_service.refresh(
                puuid=puuid,
                training_history=archived_cycles,
                current_mission=pipeline.mission,
            )
        )

        learning_state = (
            memory_service.public_payload(
                pedagogical_memory
            )
        )

        comparison_data["training"] = _training_payload(
            pipeline,
            history=training_history,
            learning_state=learning_state,
        )

        assessments = SkillMappingService.assess(
            performance=analysis.performance,
        )

        priority_skill_id = (
            pipeline.training_plan.primary_skill_id
            if pipeline.training_plan is not None
            else pipeline.mission.skill_id
        )

        comparison_data["adaptive_coach"] = (
            AdaptiveCoachIntelligenceService.build(
                puuid=puuid,
                assessments=assessments,
                pedagogical_memory=pedagogical_memory,
                training_history=archived_cycles,
                priority_skill_id=priority_skill_id,
                current_task_id=pipeline.mission.task.id,
                player_repository=training_repository,
                persist_profile=True,
            )
        )

        # Fase 12.7 — Progress Dashboard.
        # O Adaptive Coach já persistiu o Learning Profile oficial.
        # A camada longitudinal apenas fotografa esse estado; não recalcula Skills.
        player_directory = training_repository.get_player_directory(
            puuid=puuid
        )

        learning_profile = comparison_data["adaptive_coach"].get(
            "profile",
            {},
        )

        progress_history = ProgressHistoryService.load(
            player_directory=player_directory
        )

        latest_snapshot = (
            progress_history[-1]
            if progress_history
            else None
        )

        candidate_snapshot = ProgressSnapshotService.build(
            learning_profile=learning_profile,
            archived_cycles_total=len(archived_cycles),
            metadata={
                "source": "benchmark_compare",
                "match_count": request.match_count,
                "benchmark_id": benchmark_id,
            },
        )

        # Evita criar um snapshot novo a cada refresh da página.
        # Só registra quando o estado pedagógico longitudinal mudou.
        latest_signature = (
            (
                latest_snapshot.priority_skill_id,
                latest_snapshot.archived_cycles_total,
                latest_snapshot.skills,
            )
            if latest_snapshot is not None
            else None
        )
        candidate_signature = (
            candidate_snapshot.priority_skill_id,
            candidate_snapshot.archived_cycles_total,
            candidate_snapshot.skills,
        )

        milestones = []

        if latest_signature != candidate_signature:
            ProgressHistoryService.append(
                player_directory=player_directory,
                snapshot=candidate_snapshot,
            )

            milestones = ProgressMilestoneService.detect(
                previous=latest_snapshot,
                current=candidate_snapshot,
            )

            progress_history = ProgressHistoryService.load(
                player_directory=player_directory
            )

        progress_intelligence = ProgressIntelligenceService.build(
            snapshots=progress_history,
            primary_skill_id=priority_skill_id,
        )

        progress_intelligence["milestones"] = [
            item.to_dict()
            for item in milestones
        ]
        progress_intelligence["snapshot_count"] = len(
            progress_history
        )

        comparison_data["progress"] = progress_intelligence

        # Fase 13.5-13.7 — o histórico passa a orientar COMO abordar o treino.
        # A Skill continua vindo exclusivamente do Learning Priority.
        comparison_data["progress_aware_coach"] = ProgressAwareCoachService.build(
            progress=progress_intelligence,
            priority_skill_id=priority_skill_id,
            adaptive_strategy=comparison_data["adaptive_coach"].get("strategy", {}),
        )

        return BenchmarkCompareResponse.model_validate(comparison_data)

    except (ValueError, RuntimeError, KeyError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
