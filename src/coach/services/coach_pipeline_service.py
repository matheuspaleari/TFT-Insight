from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.inspector import InspectorEngine
from src.learning import LearningEngine, SkillMappingService
from src.learning.services.habit_engine import HabitEngine
from src.learning.services.habit_skill_mapping_service import HabitSkillMappingService
from src.learning.services.learning_priority_engine import LearningPriorityEngine
from src.learning.services.skill_evidence_fusion_service import SkillEvidenceFusionService
from src.training import PlayerTrainingService
from src.training.services.training_plan_engine import TrainingPlanEngine
from src.training.services.training_plan_mission_adapter import TrainingPlanMissionAdapter
from src.training.services.mission_cycle_stage_resolver import MissionCycleStageResolver
from src.coach.services.coach_context_fusion_service import (
    CoachContextFusionService,
)


@dataclass(frozen=True)
class CoachPipelineResult:
    assessments: tuple[Any, ...]
    inspections: tuple[Any, ...]
    recommendation: Any
    habits: tuple[Any, ...]
    signals: tuple[Any, ...]
    fusion_results: tuple[Any, ...]
    priority_plan: Any
    training_plan: Any
    mission: Any
    coach_message: str
    cycle_stage: str
    cycle_stage_label: str
    cycle_message: str
    context_fusion: dict[str, Any]


class CoachPipelineService:
    def __init__(self, player_training_service: PlayerTrainingService | None = None) -> None:
        self.player_training_service = player_training_service or PlayerTrainingService()

    def run(
        self,
        *,
        puuid: str,
        performance,
        coach_context,
        current_match_ids: tuple[str, ...],
        mission_games_target: int = 5,
        competitive_spectrum: dict[str, Any] | None = None,
    ) -> CoachPipelineResult:
        assessments = SkillMappingService.assess(performance=performance)
        inspections = InspectorEngine.inspect_all(
            assessments=assessments,
            performance=performance,
        )
        recommendation = LearningEngine.recommend(assessments=assessments)

        self.player_training_service.sync_mission_progress(
            puuid=puuid,
            current_match_ids=current_match_ids,
        )

        habits = HabitEngine.detect(coach_context=coach_context)
        signals = HabitSkillMappingService.map(habits=habits)
        fusion_results = tuple(
            SkillEvidenceFusionService.fuse(
                assessments=assessments,
                signals=signals,
            )
        )
        priority_plan = LearningPriorityEngine.build(
            fusion_results=fusion_results
        )
        training_plan = TrainingPlanEngine.build(
            priority_plan=priority_plan,
            games_target=mission_games_target,
        )

        baseline = tuple(current_match_ids)

        if training_plan is not None:
            desired_task = TrainingPlanMissionAdapter.select_task(
                training_plan=training_plan
            )
            mission = self.player_training_service.get_or_create_mission_from_plan(
                puuid=puuid,
                training_plan=training_plan,
                baseline_match_ids=baseline,
            )

            if mission.task.id == desired_task.id:
                coach_message = (
                    f"Seu foco atual será {training_plan.primary_skill_label}. "
                    f"Nas próximas {mission.games_target} partidas, pratique apenas "
                    f"o exercício “{mission.title}”. {mission.task.habit} "
                    f"{training_plan.objective} "
                    "Não tente corrigir várias coisas ao mesmo tempo."
                )
            else:
                coach_message = (
                    f"Continue sua missão atual “{mission.title}” por mais "
                    f"{mission.remaining_games} partida(s). Uma nova prioridade já "
                    f"foi identificada ({training_plan.primary_skill_label}), mas "
                    "ela só será transformada em nova missão depois que o ciclo atual terminar."
                )
        else:
            mission = self.player_training_service.get_or_create_mission(
                puuid=puuid,
                recommendation=recommendation,
                games_target=mission_games_target,
                baseline_match_ids=baseline,
            )
            coach_message = (
                f"Seu foco atual será {recommendation.skill.title}. "
                f"Nas próximas {mission.games_target} partidas, pratique apenas "
                f"o exercício “{mission.title}”. {mission.task.habit} "
                "Não tente corrigir várias coisas ao mesmo tempo."
            )

        cycle_state = MissionCycleStageResolver.resolve(
            games_completed=mission.games_completed,
            games_target=mission.games_target,
        )

        context_fusion = CoachContextFusionService.build(
            priority_plan=priority_plan,
            training_plan=training_plan,
            mission=mission,
            competitive_spectrum=competitive_spectrum,
            coach_context=coach_context,
        )

        return CoachPipelineResult(
            assessments=tuple(assessments),
            inspections=tuple(inspections),
            recommendation=recommendation,
            habits=tuple(habits),
            signals=tuple(signals),
            fusion_results=fusion_results,
            priority_plan=priority_plan,
            training_plan=training_plan,
            mission=mission,
            coach_message=coach_message,
            cycle_stage=cycle_state.stage.value,
            cycle_stage_label=cycle_state.label,
            cycle_message=cycle_state.message,
            context_fusion=context_fusion,
        )
