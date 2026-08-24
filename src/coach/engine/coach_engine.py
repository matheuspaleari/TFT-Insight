from __future__ import annotations

from pathlib import Path

from src.coach.models import CoachReport
from src.coach.services.coach_pipeline_service import CoachPipelineService
from src.integration_engine.services.benchmark_coach_context_builder import BenchmarkCoachContextBuilder
from src.integration_engine.services.cached_match_service import CachedMatchService
from src.services import PlayerAnalysisService
from src.training import PlayerTrainingService


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class CoachEngine:
    def __init__(
        self,
        player_analysis_service: PlayerAnalysisService | None = None,
        player_training_service: PlayerTrainingService | None = None,
        cached_match_service: CachedMatchService | None = None,
        project_root: Path | None = None,
        pipeline_service: CoachPipelineService | None = None,
    ) -> None:
        self.player_analysis_service = player_analysis_service or PlayerAnalysisService()
        self.player_training_service = player_training_service or PlayerTrainingService()
        self.project_root = project_root or PROJECT_ROOT
        self.cached_match_service = cached_match_service or CachedMatchService(
            project_root=self.project_root
        )
        self.pipeline_service = pipeline_service or CoachPipelineService(
            player_training_service=self.player_training_service
        )

    def analyze(
        self,
        *,
        game_name: str,
        tag_line: str,
        benchmark_id: str | None = None,
        match_count: int = 10,
        use_cache: bool = True,
        mission_games_target: int = 5,
    ) -> CoachReport:
        analysis = self.player_analysis_service.analyze(
            game_name=game_name,
            tag_line=tag_line,
            benchmark_id=benchmark_id,
            match_count=match_count,
            use_cache=use_cache,
        )

        match_result = self.cached_match_service.load_player_matches(
            puuid=analysis.puuid,
            count=match_count,
        )

        coach_context = BenchmarkCoachContextBuilder.build(
            project_root=self.project_root,
            matches=match_result.matches,
        )

        pipeline = self.pipeline_service.run(
            puuid=analysis.puuid,
            performance=analysis.performance,
            coach_context=coach_context,
            current_match_ids=tuple(analysis.match_ids),
            mission_games_target=mission_games_target,
            competitive_spectrum=(
                analysis.competitive_spectrum
                if isinstance(
                    analysis.competitive_spectrum,
                    dict,
                )
                else None
            ),
        )

        return CoachReport(
            analysis=analysis,
            skill_assessments=pipeline.assessments,
            skill_inspections=pipeline.inspections,
            learning_recommendation=pipeline.recommendation,
            mission=pipeline.mission,
            coach_message=pipeline.coach_message,
        )
