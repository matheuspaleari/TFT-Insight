from pathlib import Path

from src.role_inference import (
    CommunityDragonItemParser,
    ItemCatalogClassifier,
    ItemObservationRepository,
    RichItemRepository,
)


class ItemClassificationProvider:
    """
    Carrega a classificação de itens uma vez por processo.

    O CommunityDragon e as observações Challenger são lidos do cache local.
    Nenhuma chamada externa é feita por este provider.
    """

    _classifications = None

    def __init__(
        self,
        *,
        project_root: Path,
    ) -> None:
        self.project_root = project_root

    def get(self):
        if self.__class__._classifications is not None:
            return self.__class__._classifications

        rich_repository = RichItemRepository()

        if not rich_repository.exists():
            raise RuntimeError(
                "Cache do CommunityDragon não encontrado. "
                "Execute primeiro a atualização dos dados estáticos."
            )

        observations_path = (
            self.project_root
            / "data"
            / "role_inference"
            / "challenger"
            / "item_observations.json"
        )

        observations = ItemObservationRepository(
            path=observations_path
        ).load_all()

        if not observations:
            raise RuntimeError(
                "Observações Challenger de itens não encontradas em "
                f"{observations_path}."
            )

        rich_items = CommunityDragonItemParser.parse(
            rich_repository.load()
        )

        self.__class__._classifications = (
            ItemCatalogClassifier.classify_all(
                items=rich_items,
                observations=observations,
            )
        )

        return self.__class__._classifications
