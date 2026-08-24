from __future__ import annotations

from ..models.player_development_summary import (
    PlayerDevelopmentSummary,
)


class OverallPlayerDevelopmentService:
    """
    Resume o desenvolvimento sem fazer média simples de Skills.
    """

    @classmethod
    def summarize(
        cls,
        *,
        timelines: dict,
        primary_skill_id: str | None,
    ) -> PlayerDevelopmentSummary:
        improving = []
        stable = []
        regressing = []
        insufficient = []

        for skill_id, points in timelines.items():
            if not points:
                insufficient.append(skill_id)
                continue

            latest = points[-1]
            trend = str(latest.trend).upper()

            if len(points) < 2:
                insufficient.append(skill_id)
                continue

            if trend == "IMPROVING":
                improving.append(skill_id)
            elif trend == "REGRESSING":
                regressing.append(skill_id)
            elif trend == "STABLE":
                stable.append(skill_id)
            else:
                insufficient.append(skill_id)

        if regressing:
            status = "NEEDS_ATTENTION"
        elif improving and not regressing:
            status = "IMPROVING"
        elif stable and not improving and not regressing:
            status = "STABLE"
        else:
            status = "INSUFFICIENT_HISTORY"

        observed = (
            len(improving)
            + len(stable)
            + len(regressing)
        )

        if observed >= 3:
            confidence = "HIGH"
        elif observed >= 1:
            confidence = "MODERATE"
        else:
            confidence = "LOW"

        rationale = (
            f"Skills melhorando: {len(improving)}; "
            f"estáveis: {len(stable)}; "
            f"regredindo: {len(regressing)}; "
            f"com histórico insuficiente: {len(insufficient)}. "
            "O estado geral não é uma média simples dos scores."
        )

        return PlayerDevelopmentSummary(
            status=status,
            confidence=confidence,
            primary_skill_id=primary_skill_id,
            improving_skills=tuple(improving),
            stable_skills=tuple(stable),
            regressing_skills=tuple(regressing),
            insufficient_skills=tuple(insufficient),
            rationale=rationale,
        )
