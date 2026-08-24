from src.performance_engine.models import UnitSnapshot
from src.role_inference.models import (
    ItemCategory,
    ItemClassification,
    RoleSeedAssessment,
    UnitRoleSeed,
)


class UnitRoleSeedInference:
    """
    Faz uma inferência inicial de papel usando apenas itens já
    classificados com confiança razoável.

    Essa etapa evita depender de listas manuais de campeões.
    """

    MIN_ITEM_CONFIDENCE = 55.0

    @classmethod
    def infer(
        cls,
        *,
        unit: UnitSnapshot,
        classifications: dict[str, ItemClassification],
    ) -> RoleSeedAssessment:
        offense = 0.0
        defense = 0.0
        utility = 0.0
        considered = 0
        evidence = []

        for item_id in unit.items:
            classification = classifications.get(
                item_id
            )

            if (
                classification is None
                or classification.confidence
                < cls.MIN_ITEM_CONFIDENCE
            ):
                continue

            considered += 1

            offense += (
                classification.offense_score
            )
            defense += (
                classification.defense_score
            )
            utility += (
                classification.utility_score
            )

            evidence.append(
                f"{item_id}: "
                f"{classification.category.value} "
                f"({classification.confidence:.0f}%)"
            )

        if considered == 0:
            return RoleSeedAssessment(
                role=UnitRoleSeed.UNKNOWN,
                confidence=0.0,
                offense_score=0.0,
                defense_score=0.0,
                utility_score=0.0,
                evidence=(
                    "nenhum item com confiança suficiente",
                ),
            )

        offense /= considered
        defense /= considered
        utility /= considered

        scores = {
            UnitRoleSeed.DAMAGE_CARRY: offense,
            UnitRoleSeed.TANK: defense,
            UnitRoleSeed.SUPPORT: utility,
        }

        ordered = sorted(
            scores.values(),
            reverse=True,
        )

        role = max(
            scores,
            key=scores.get,
        )

        margin = (
            ordered[0] - ordered[1]
            if len(ordered) > 1
            else ordered[0]
        )

        confidence = min(
            100.0,
            45.0
            + considered * 12.0
            + margin * 0.35,
        )

        if ordered[0] < 25.0 or margin < 8.0:
            role = UnitRoleSeed.UNKNOWN
            confidence = min(
                confidence,
                49.0,
            )

        return RoleSeedAssessment(
            role=role,
            confidence=round(confidence, 2),
            offense_score=round(offense, 2),
            defense_score=round(defense, 2),
            utility_score=round(utility, 2),
            evidence=tuple(evidence),
        )
