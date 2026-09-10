from __future__ import annotations

from src.role_inference.models import (
    ItemCategory,
    ItemClassification,
    ItemObservation,
    RichItemData,
)
from src.role_inference.repositories.item_manual_catalog_repository import (
    ItemManualCatalogRepository,
)

from .hybrid_item_classifier import HybridItemClassifier


class ItemCatalogClassifier:
    """
    Classificador de itens com autoridade manual para o Set 18.

    Prioridade:
    1. item_catalog_v2.json;
    2. classificador híbrido legado para itens ausentes do catálogo.

    O benchmark Challenger continua disponível como evidência secundária
    somente para itens sem classificação manual. Ele nunca sobrescreve
    carry/tank/support definidos no catálogo V2.
    """

    MANUAL_CONFIDENCE = 100.0

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

        repository = ItemManualCatalogRepository()
        manual_items = repository.load_items()

        classifications: dict[
            str,
            ItemClassification,
        ] = {}

        # O catálogo manual entra primeiro e independe da presença
        # do item no payload do CommunityDragon.
        for item_id, catalog_item in manual_items.items():
            classifications[item_id] = (
                cls._classification_from_manual(
                    item_id=item_id,
                    catalog_item=catalog_item,
                )
            )

        # Itens novos/desconhecidos continuam usando a pipeline antiga.
        # Isso mantém o sistema resiliente a mudanças futuras sem permitir
        # que o aprendizado altere decisões já verificadas manualmente.
        for item_id, item in items.items():
            if item_id in classifications:
                continue

            classifications[item_id] = (
                HybridItemClassifier.classify(
                    item=item,
                    observation=observation_map.get(
                        item_id
                    ),
                )
            )

        return classifications

    @classmethod
    def _classification_from_manual(
        cls,
        *,
        item_id: str,
        catalog_item: dict,
    ) -> ItemClassification:
        offense = float(
            catalog_item["carry_weight"]
        )
        defense = float(
            catalog_item["tank_weight"]
        )
        utility = float(
            catalog_item["support_weight"]
        )

        category = cls._manual_category(
            manual_category=str(
                catalog_item.get(
                    "manual_category",
                    "",
                )
            ),
            offense=offense,
            defense=defense,
            utility=utility,
        )

        display_name = str(
            catalog_item.get(
                "display_name",
                item_id,
            )
        ).strip()

        role_label = str(
            catalog_item.get(
                "manual_role_label",
                "",
            )
        ).strip()

        learning_enabled = bool(
            catalog_item.get(
                "learning_enabled",
                False,
            )
        )

        evidence = [
            f"catálogo manual Set 18: {display_name}",
        ]

        if role_label:
            evidence.append(
                f"função verificada: {role_label}"
            )

        evidence.append(
            "pesos manuais: "
            f"carry={offense:.0f}, "
            f"tank={defense:.0f}, "
            f"support={utility:.0f}"
        )

        if not learning_enabled:
            evidence.append(
                "aprendizado estatístico desativado "
                "para este item"
            )

        inherited_from = str(
            catalog_item.get(
                "inherits_from",
                "",
            )
        ).strip()

        if inherited_from:
            evidence.append(
                "função herdada do item-base verificado"
            )

        return ItemClassification(
            item_id=item_id,
            category=category,
            confidence=cls.MANUAL_CONFIDENCE,
            offense_score=offense,
            defense_score=defense,
            utility_score=utility,
            evidence=tuple(evidence),
            source="manual_set18_catalog_v2",
        )

    @staticmethod
    def _manual_category(
        *,
        manual_category: str,
        offense: float,
        defense: float,
        utility: float,
    ) -> ItemCategory:
        normalized = (
            manual_category
            .strip()
            .lower()
        )

        # Categorias explicitamente híbridas/flexíveis têm prioridade
        # sobre o maior peso individual.
        if (
            "hybrid" in normalized
            or "híbrido" in normalized
            or "neutral" in normalized
            or "neutro" in normalized
            or "emblem" in normalized
        ):
            return ItemCategory.HYBRID

        if "support" in normalized:
            return ItemCategory.UTILITY

        if "tank" in normalized:
            return ItemCategory.DEFENSE

        if "carry" in normalized:
            return ItemCategory.OFFENSE

        # Componentes e categorias auxiliares seguem os pesos aprovados.
        scores = {
            ItemCategory.OFFENSE: offense,
            ItemCategory.DEFENSE: defense,
            ItemCategory.UTILITY: utility,
        }

        maximum = max(scores.values())

        winners = [
            category
            for category, score in scores.items()
            if score == maximum
        ]

        if len(winners) != 1:
            return ItemCategory.HYBRID

        return winners[0]
