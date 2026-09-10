from src.performance_engine.models import Match
from src.role_inference.models import (
    ItemClassification,
    ItemObservation,
    RichItemData,
)
from src.role_inference.repositories import (
    ItemObservationRepository,
)

from .item_catalog_classifier import ItemCatalogClassifier
from .item_observation_collector import ItemObservationCollector


class ItemLearningCycle:
    """
    Executa um ciclo seguro de refinamento.

    1. classifica itens com autoridade manual V2 + fallback legado;
    2. infere papéis-semente das unidades;
    3. coleta apenas observações permitidas pelo catálogo;
    4. persiste as observações;
    5. recalcula as classificações.

    O aprendizado Challenger é evidência secundária e nunca substitui a
    autoridade estrutural do catálogo manual.
    """

    def __init__(
        self,
        *,
        observation_repository: ItemObservationRepository,
    ) -> None:
        self.observation_repository = observation_repository

    def run(
        self,
        *,
        matches: list[Match],
        items: dict[str, RichItemData],
    ) -> tuple[
        dict[str, ItemClassification],
        dict[str, ItemObservation],
    ]:
        existing = self.observation_repository.load_all()

        initial_classifications = ItemCatalogClassifier.classify_all(
            items=items,
            observations=existing,
        )

        updated_observations = ItemObservationCollector.collect(
            matches=matches,
            item_classifications=initial_classifications,
            existing=existing,
        )

        self.observation_repository.save_all(updated_observations)

        final_classifications = ItemCatalogClassifier.classify_all(
            items=items,
            observations=updated_observations,
        )

        return final_classifications, updated_observations
