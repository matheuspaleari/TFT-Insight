from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.decision_engine import ContestAnalyzer
from src.integration_engine.api.dependencies import require_api_key
from src.integration_engine.services.cached_match_service import CachedMatchService
from src.post_match import PersonalBaselineService, PostMatchAnalysisService
from src.post_match.services.historical_context_interpretation_service import HistoricalContextInterpretationService
from src.post_match.services.historical_match_context_service import HistoricalMatchContextService
from src.post_match.services.post_match_interpretation_service import PostMatchInterpretationService
from src.post_match.services.post_match_report_service import PostMatchReportService
from src.action_signal import ActionSignalEngine
from src.contextual_recommendation import ContextualRecommendationEngine
from src.recommendation_guardrails import RecommendationGuardrails
from src.next_match_plan import NextMatchPlanService

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class PostMatchPlayerRequest(BaseModel):
    game_name: str = Field(min_length=1)
    tag_line: str = Field(min_length=1)


class PostMatchTrainingRequest(BaseModel):
    skill_id: str = "leveling"
    skill_label: str = "Leveling"
    mission_title: str = "Planejar o próximo nível"
    objective: str = ""


class PostMatchReportRequest(BaseModel):
    player: PostMatchPlayerRequest
    training: PostMatchTrainingRequest
    history_size: int = Field(default=10, ge=10, le=20)
    competitive_context: dict = Field(default_factory=dict)
    coach_fusion: dict = Field(default_factory=dict)


router = APIRouter(
    prefix="/v1/post-match",
    tags=["post-match-analysis"],
)


@router.post("/player/latest")
def latest_post_match_report(
    request: PostMatchReportRequest,
    _: str = Depends(require_api_key),
) -> dict:
    try:
        loader = CachedMatchService(project_root=PROJECT_ROOT)
        puuid = loader.resolve_puuid(
            puuid=None,
            game_name=request.player.game_name,
            tag_line=request.player.tag_line,
        )

        result = loader.load_player_matches(
            puuid=puuid,
            count=request.history_size + 1,
        )
        matches = list(result.matches)

        if len(matches) < 11:
            raise ValueError(
                "A análise pós-partida precisa de pelo menos "
                "11 partidas válidas: 1 atual + 10 anteriores."
            )

        target = matches[0]
        history = matches[1:request.history_size + 1]

        training = {
            "primary_skill_id": request.training.skill_id,
            "primary_skill_label": request.training.skill_label,
            "mission_title": request.training.mission_title,
            "objective": request.training.objective,
        }

        analysis = PostMatchAnalysisService.analyze(
            match=target,
            training=training,
            contest_report=ContestAnalyzer.analyze(target),
        )

        baseline = PersonalBaselineService.compare(
            target_match=target,
            prior_matches=history,
            requested_history_size=request.history_size,
        )

        post_interpretation = PostMatchInterpretationService.interpret(
            analysis=analysis,
            baseline=baseline,
        )

        historical = HistoricalMatchContextService.analyze(
            target_match=target,
            prior_matches=history,
            baseline_report=baseline,
        )

        historical_interpretation = HistoricalContextInterpretationService.interpret(
            historical_context=historical,
            active_skill_id=request.training.skill_id,
            active_skill_label=request.training.skill_label,
        )

        report = PostMatchReportService.build(
            analysis=analysis,
            baseline=baseline,
            post_match_interpretation=post_interpretation,
            historical_context=historical,
            historical_interpretation=historical_interpretation,
        )

        action_signals = ActionSignalEngine.build(
            post_match_report=report,
            post_match_analysis=analysis,
            historical_context=historical,
            active_skill_id=request.training.skill_id,
            active_skill_label=request.training.skill_label,
            mission_title=request.training.mission_title,
        )

        contextual_recommendation = ContextualRecommendationEngine.build(
            action_signals=action_signals,
            competitive_context=request.competitive_context,
            coach_fusion=request.coach_fusion,
            active_skill_label=request.training.skill_label,
            mission_title=request.training.mission_title,
        )

        guardrails = RecommendationGuardrails.validate(
            recommendation=contextual_recommendation,
            action_signals=action_signals,
            active_skill_label=request.training.skill_label,
            mission_title=request.training.mission_title,
            direct_evidence_count=analysis.direct_count,
        )

        next_match_plan = NextMatchPlanService.build(
            recommendation=contextual_recommendation,
            guardrails=guardrails,
            active_skill_label=request.training.skill_label,
            mission_title=request.training.mission_title,
            mission_objective=request.training.objective,
        )

        payload = report.to_dict()
        payload["action_signals"] = action_signals.to_dict()
        payload["contextual_recommendation"] = contextual_recommendation.to_dict()
        payload["recommendation_guardrails"] = guardrails.to_dict()
        payload["next_match_plan"] = {
            "active_skill_label": next_match_plan.active_skill_label,
            "mission_title": next_match_plan.mission_title,
            "mission_objective": next_match_plan.mission_objective,
            "primary_title": next_match_plan.primary_title,
            "primary_action": next_match_plan.primary_action,
            "watch_items": list(next_match_plan.watch_items),
            "preserve": next_match_plan.preserve,
            "coach_reminder": next_match_plan.coach_reminder,
            "publishable": next_match_plan.publishable,
            "blocked_reason": next_match_plan.blocked_reason,
            "protections": {
                "changes_learning_priority": next_match_plan.changes_learning_priority,
                "changes_mission": next_match_plan.changes_mission,
                "changes_difficulty": next_match_plan.changes_difficulty,
                "changes_evidence_class": next_match_plan.changes_evidence_class,
                "counts_as_mission_evidence": next_match_plan.counts_as_mission_evidence,
                "predicts_rank_up": next_match_plan.predicts_rank_up,
            },
        }
        payload["player"] = {
            "game_name": request.player.game_name,
            "tag_line": request.player.tag_line,
        }
        payload["match"] = {
            "match_id": str(target.match_id),
            "placement": int(target.placement),
            "level": int(target.level),
            "gold_left": int(target.gold_left),
            "last_round": int(target.last_round),
            "players_eliminated": int(target.players_eliminated),
            "total_damage_to_players": int(target.total_damage_to_players),
        }
        payload["internal"] = {
            "verdict": analysis.verdict.value,
            "evidence_summary": {
                "direct": analysis.direct_count,
                "proxy": analysis.proxy_count,
                "context": analysis.context_count,
                "unavailable": analysis.unavailable_count,
            },
            "historical_signals": [
                {
                    "metric_id": item.metric_id,
                    "signal": item.signal.value,
                }
                for item in historical.metrics
            ],
        }
        return payload

    except (ValueError, RuntimeError, KeyError, AttributeError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
