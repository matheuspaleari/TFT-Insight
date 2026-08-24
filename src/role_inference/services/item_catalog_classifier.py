from src.role_inference.models import (
    ItemClassification,
    ItemObservation,
    RichItemData,
)

from .hybrid_item_classifier import (
    HybridItemClassifier,
)


class ItemCatalogClassifier:
    """
    Classifica todos os itens completos conhecidos.
    """

    @classmethod
    def classify_all(
        cls,
        *,
        items: dict[str, RichItemData],
        observations: dict[
            str,
            ItemObservation,
        ] | None = None,
    ) -> dict[str, ItemClassification]:
        observation_map = observations or {}

        return {
            item_id: HybridItemClassifier.classify(
                item=item,
                observation=observation_map.get(
                    item_id
                ),
            )
            for item_id, item in items.items()
        }
