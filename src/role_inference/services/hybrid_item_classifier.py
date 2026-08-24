from src.role_inference.models import (
    ItemCategory,
    ItemClassification,
    ItemObservation,
    RichItemData,
)

from .metadata_item_classifier import MetadataItemClassifier
from .statistical_item_classifier import StatisticalItemClassifier


class HybridItemClassifier:
    """
    Combina metadados completos e padrões dos benchmarks.

    Metadados têm maior peso no início. Conforme a amostra estatística
    cresce, os padrões observados passam a influenciar mais.
    """

    @classmethod
    def classify(
        cls,
        *,
        item: RichItemData,
        observation: ItemObservation | None = None,
    ) -> ItemClassification:
        metadata = MetadataItemClassifier.classify(item)

        if observation is None:
            return metadata

        statistical = StatisticalItemClassifier.classify(
            observation
        )

        if statistical.confidence == 0:
            return metadata

        statistical_weight = min(
            0.60,
            observation.total_uses / 200.0,
        )
        metadata_weight = 1.0 - statistical_weight

        offense = (
            metadata.offense_score * metadata_weight
            + statistical.offense_score * statistical_weight
        )
        defense = (
            metadata.defense_score * metadata_weight
            + statistical.defense_score * statistical_weight
        )
        utility = (
            metadata.utility_score * metadata_weight
            + statistical.utility_score * statistical_weight
        )

        values = {
            ItemCategory.OFFENSE: offense,
            ItemCategory.DEFENSE: defense,
            ItemCategory.UTILITY: utility,
        }

        ordered = sorted(
            values.values(),
            reverse=True,
        )

        category = max(
            values,
            key=values.get,
        )

        if ordered[0] - ordered[1] < 12:
            category = ItemCategory.HYBRID

        confidence = min(
            100.0,
            metadata.confidence * metadata_weight
            + statistical.confidence * statistical_weight,
        )

        return ItemClassification(
            item_id=item.item_id,
            category=category,
            confidence=round(confidence, 2),
            offense_score=round(offense, 2),
            defense_score=round(defense, 2),
            utility_score=round(utility, 2),
            evidence=(
                *metadata.evidence,
                *statistical.evidence,
                (
                    "peso estatístico: "
                    f"{statistical_weight:.0%}"
                ),
            ),
            source="hybrid",
        )
