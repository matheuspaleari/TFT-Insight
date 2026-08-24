from __future__ import annotations
from .progress_coaching_context_service import ProgressCoachingContextService
from .progress_aware_strategy_engine import ProgressAwareStrategyEngine
from .training_adaptation_service import TrainingAdaptationService
from .progress_aware_explanation_service import ProgressAwareExplanationService

class ProgressAwareCoachService:
    @classmethod
    def build(cls, *, progress: dict, priority_skill_id: str, adaptive_strategy: dict | None = None) -> dict:
        adaptive_strategy = adaptive_strategy if isinstance(adaptive_strategy, dict) else {}
        context = ProgressCoachingContextService.build(progress=progress, priority_skill_id=priority_skill_id)
        strategy = ProgressAwareStrategyEngine.decide(context=context, adaptive_strategy=adaptive_strategy)
        context_payload = context.to_dict(); strategy_payload = strategy.to_dict()
        adaptation = TrainingAdaptationService.build(progress_strategy=strategy_payload, adaptive_strategy=adaptive_strategy)
        explanation = ProgressAwareExplanationService.build(context=context_payload, strategy=strategy_payload, adaptation=adaptation)
        return {"context": context_payload, "strategy": strategy_payload, "adaptation": adaptation, "explanation": explanation}
