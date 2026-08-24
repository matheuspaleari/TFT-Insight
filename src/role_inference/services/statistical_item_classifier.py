from src.role_inference.models import (
    ItemCategory,
    ItemClassification,
    ItemObservation,
)


class StatisticalItemClassifier:
    MINIMUM_USES = 20

    @classmethod
    def classify(
        cls,
        observation: ItemObservation,
    ) -> ItemClassification:
        total = max(
            observation.total_uses,
            observation.damage_carry_uses
            + observation.tank_uses
            + observation.support_uses,
        )

        if total < cls.MINIMUM_USES:
            return ItemClassification(
                item_id=observation.item_id,
                category=ItemCategory.UNKNOWN,
                confidence=0.0,
                offense_score=0.0,
                defense_score=0.0,
                utility_score=0.0,
                evidence=(
                    f"amostra insuficiente: {total} usos",
                ),
                source="benchmark_statistics",
            )

        offense = (
            observation.damage_carry_uses
            / total
            * 100.0
        )
        defense = (
            observation.tank_uses
            / total
            * 100.0
        )
        utility = (
            observation.support_uses
            / total
            * 100.0
        )

        scores = {
            ItemCategory.OFFENSE: offense,
            ItemCategory.DEFENSE: defense,
            ItemCategory.UTILITY: utility,
        }

        category = max(
            scores,
            key=scores.get,
        )

        ordered = sorted(
            scores.values(),
            reverse=True,
        )

        if ordered[0] - ordered[1] < 10:
            category = ItemCategory.HYBRID

        confidence = min(
            100.0,
            40.0 + total / 2.0,
        )

        return ItemClassification(
            item_id=observation.item_id,
            category=category,
            confidence=round(confidence, 2),
            offense_score=round(offense, 2),
            defense_score=round(defense, 2),
            utility_score=round(utility, 2),
            evidence=(
                f"{total} usos observados",
                f"carry: {observation.damage_carry_uses}",
                f"tank: {observation.tank_uses}",
                f"support: {observation.support_uses}",
            ),
            source="benchmark_statistics",
        )
