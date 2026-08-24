from __future__ import annotations

from src.coach_intelligence.models.skill_evolution import (
    SkillEvolution,
)


class SkillEvolutionEngine:
    MIN_RELEVANT_DELTA = 5.0

    @classmethod
    def compare(
        cls,
        *,
        current_profile,
        previous_profile: dict | None,
    ) -> tuple[SkillEvolution, ...]:
        previous_skills = {}

        if isinstance(
            previous_profile,
            dict,
        ):
            raw = previous_profile.get(
                "skills",
                {},
            )
            if isinstance(
                raw,
                dict,
            ):
                previous_skills = raw

        results = []

        for current in current_profile.skills:
            previous = previous_skills.get(
                current.skill_id,
                {},
            )

            if not isinstance(
                previous,
                dict,
            ):
                previous = {}

            previous_score = previous.get(
                "score"
            )

            if previous_score is not None:
                previous_score = float(
                    previous_score
                )

            delta = (
                None
                if (
                    previous_score is None
                    or current.score is None
                )
                else (
                    float(current.score)
                    - previous_score
                )
            )

            direction = cls._direction(
                delta=delta,
                trend=current.trend,
            )

            confidence = cls._confidence(
                delta=delta,
                trend_confidence=(
                    current.trend_confidence
                ),
            )

            results.append(
                SkillEvolution(
                    skill_id=current.skill_id,
                    previous_score=previous_score,
                    current_score=current.score,
                    score_delta=delta,
                    previous_level=(
                        previous.get(
                            "level"
                        )
                    ),
                    current_level=current.level,
                    training_trend=current.trend,
                    direction=direction,
                    confidence=confidence,
                    rationale=cls._rationale(
                        delta=delta,
                        trend=current.trend,
                        direction=direction,
                    ),
                )
            )

        return tuple(
            results
        )

    @classmethod
    def _direction(
        cls,
        *,
        delta: float | None,
        trend: str,
    ) -> str:
        trend = str(
            trend
        ).upper()

        if delta is None:
            if trend == "IMPROVING":
                return "IMPROVING"
            if trend == "REGRESSING":
                return "REGRESSING"
            if trend == "STABLE":
                return "STABLE"
            return "INSUFFICIENT_HISTORY"

        if delta >= cls.MIN_RELEVANT_DELTA:
            return "IMPROVING"

        if delta <= -cls.MIN_RELEVANT_DELTA:
            return "REGRESSING"

        if trend == "IMPROVING":
            return "IMPROVING"

        if trend == "REGRESSING":
            return "REGRESSING"

        return "STABLE"

    @staticmethod
    def _confidence(
        *,
        delta: float | None,
        trend_confidence: str,
    ) -> str:
        if delta is None:
            return str(
                trend_confidence
            ).upper()

        if str(
            trend_confidence
        ).upper() in {
            "HIGH",
            "MODERATE",
        }:
            return "MODERATE"

        return "LOW"

    @staticmethod
    def _rationale(
        *,
        delta: float | None,
        trend: str,
        direction: str,
    ) -> str:
        if delta is None:
            return (
                "Não existe snapshot técnico anterior comparável; "
                f"a leitura usa apenas a tendência de treino {trend}."
            )

        return (
            f"O score técnico variou {delta:+.2f} pontos e a "
            f"tendência de treino é {trend}. A direção consolidada "
            f"foi classificada como {direction}."
        )
