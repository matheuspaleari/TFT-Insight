from __future__ import annotations
from src.progress_aware_coach.models.progress_coaching_context import ProgressCoachingContext

class ProgressCoachingContextService:
    """Fase 13.1: transforma a timeline da Skill prioritária em contexto pedagógico."""

    MIN_REACTION_SNAPSHOTS = 3
    MIN_STRONG_SNAPSHOTS = 4
    MATERIAL_DELTA = 5.0

    @classmethod
    def build(cls, *, progress: dict, priority_skill_id: str) -> ProgressCoachingContext:
        timelines = progress.get("timelines", {}) if isinstance(progress, dict) else {}
        points = timelines.get(priority_skill_id, []) if isinstance(timelines, dict) else []
        valid = [p for p in points if isinstance(p, dict) and isinstance(p.get("score"), (int, float))]
        n = len(valid)
        if not valid:
            return ProgressCoachingContext(priority_skill_id, 0, None, None, None, "UNKNOWN", "INSUFFICIENT_HISTORY", "LOW", 0, False, "Não existem snapshots avaliáveis para a Skill prioritária.")

        first = float(valid[0]["score"]); latest = float(valid[-1]["score"]); delta = latest-first
        moves = []
        for a,b in zip(valid, valid[1:]):
            d=float(b["score"])-float(a["score"])
            moves.append("UP" if d > 0.5 else "DOWN" if d < -0.5 else "FLAT")
        recent = moves[-1] if moves else "UNKNOWN"
        consecutive = 0
        if moves and recent in {"UP","DOWN"}:
            for m in reversed(moves):
                if m == recent: consecutive += 1
                else: break

        if n < cls.MIN_REACTION_SNAPSHOTS:
            signal, conf, react = "WATCH", "LOW", False
            reason = f"Há {n} snapshots avaliáveis. A mudança é observada, mas ainda não sustenta adaptação do treino."
        elif recent == "DOWN" and consecutive >= 2 and delta <= -cls.MATERIAL_DELTA:
            signal = "REGRESSION"
            conf = "HIGH" if n >= cls.MIN_STRONG_SNAPSHOTS and consecutive >= 3 else "MODERATE"
            react = True
            reason = f"A Skill acumula {consecutive} movimentos de queda e delta de {delta:+.2f}."
        elif recent == "UP" and consecutive >= 2 and delta >= cls.MATERIAL_DELTA:
            signal = "IMPROVEMENT"
            conf = "HIGH" if n >= cls.MIN_STRONG_SNAPSHOTS and consecutive >= 3 else "MODERATE"
            react = True
            reason = f"A Skill acumula {consecutive} movimentos de melhora e delta de {delta:+.2f}."
        else:
            signal, conf, react = "STABLE_OR_MIXED", "MODERATE" if n >= 3 else "LOW", False
            reason = "O histórico recente é estável ou misto; não há sequência suficiente para reagir."

        return ProgressCoachingContext(priority_skill_id,n,first,latest,delta,recent,signal,conf,consecutive,react,reason)
