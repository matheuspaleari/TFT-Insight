from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class NavigationItem:
    page: str
    label: str
    icon: str
    group: str

    @property
    def display_label(self) -> str:
        return f"{self.icon} {self.label}"


class NavigationCatalog:
    """Navegação pública enxuta do TFT Insight.

    As rotas técnicas/legadas continuam no código, mas não aparecem para o
    jogador durante a fase de pré-produção.
    """

    def __init__(
        self,
        items: tuple[NavigationItem, ...],
    ) -> None:
        self.items = items

    @classmethod
    def default(cls) -> "NavigationCatalog":
        return cls(
            (
                NavigationItem(
                    page="Home",
                    label="Início",
                    icon="⌂",
                    group="Principal",
                ),
                NavigationItem(
                    page="Benchmark",
                    label="Análise",
                    icon="◆",
                    group="Principal",
                ),
                NavigationItem(
                    page="Settings",
                    label="Configurações",
                    icon="⚙",
                    group="Principal",
                ),
            )
        )

    def labels_for(
        self,
        group: str,
    ) -> tuple[str, ...]:
        return tuple(
            item.display_label
            for item in self.items
            if item.group == group
        )

    def page_from_label(
        self,
        label: str | None,
    ) -> str:
        for item in self.items:
            if item.display_label == label:
                return item.page

        return "Home"
