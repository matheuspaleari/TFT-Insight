from __future__ import annotations

from src.coach_intelligence.knowledge.cross_skill_relationships import (
    CROSS_SKILL_RELATIONSHIPS,
)
from src.coach_intelligence.models.cross_skill_insight import (
    CrossSkillInsight,
)


class CrossSkillRelationshipEngine:
    """
    Detecta combinações observadas entre Skills.

    Não atribui causalidade e não altera prioridade.
    """

    @classmethod
    def analyze(
        cls,
        *,
        profile,
    ) -> tuple[CrossSkillInsight, ...]:
        by_skill = {
            item.skill_id: item
            for item in profile.skills
        }

        insights = []

        for relationship in (
            CROSS_SKILL_RELATIONSHIPS
        ):
            source = by_skill.get(
                relationship["source"]
            )
            target = by_skill.get(
                relationship["target"]
            )

            if (
                source is None
                or target is None
                or source.score is None
                or target.score is None
            ):
                continue

            status = cls._status(
                source.score,
                target.score,
            )

            if status == "NO_SIGNAL":
                continue

            insights.append(
                CrossSkillInsight(
                    relationship_id=relationship["id"],
                    source_skill_id=source.skill_id,
                    target_skill_id=target.skill_id,
                    status=status,
                    confidence=cls._confidence(
                        source.assessment_confidence,
                        target.assessment_confidence,
                    ),
                    rationale=cls._rationale(
                        source=source,
                        target=target,
                        status=status,
                    ),
                    limitation=(
                        "A relação é apenas uma associação observada entre "
                        "Skills avaliadas. Ela não prova que uma Skill causou "
                        "o resultado da outra."
                    ),
                )
            )

        return tuple(
            insights
        )

    @staticmethod
    def _status(
        source_score: float,
        target_score: float,
    ) -> str:
        if (
            source_score >= 60.0
            and target_score < 40.0
        ):
            return "SOURCE_STRONG_TARGET_WEAK"

        if (
            source_score < 40.0
            and target_score < 40.0
        ):
            return "BOTH_NEED_ATTENTION"

        if (
            source_score >= 60.0
            and target_score >= 60.0
        ):
            return "BOTH_STRONG"

        return "NO_SIGNAL"

    @staticmethod
    def _confidence(
        source_confidence: float,
        target_confidence: float,
    ) -> str:
        minimum = min(
            float(source_confidence),
            float(target_confidence),
        )

        if minimum >= 80.0:
            return "HIGH"

        if minimum >= 60.0:
            return "MODERATE"

        return "LOW"

    @staticmethod
    def _rationale(
        *,
        source,
        target,
        status: str,
    ) -> str:
        return (
            f"{source.skill_name} está em {source.score:.2f} e "
            f"{target.skill_name} em {target.score:.2f}. "
            f"O padrão observado foi {status}."
        )
