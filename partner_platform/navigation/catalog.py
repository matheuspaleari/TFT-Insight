from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class NavigationItem:
    page: str
    label: str
    icon: str
    group: str
    admin_only: bool = False

    @property
    def display_label(self) -> str:
        return f"{self.icon} {self.label}"


class NavigationCatalog:
    """Navegação pública enxuta do TFT Insight."""

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
                NavigationItem(
                    page="Admin",
                    label="Admin",
                    icon="▣",
                    group="Principal",
                    admin_only=True,
                ),
            )
        )

    def visible_items(
        self,
        group: str,
        *,
        is_admin: bool = False,
    ) -> tuple[NavigationItem, ...]:
        return tuple(
            item
            for item in self.items
            if item.group == group
            and (not item.admin_only or is_admin)
        )

    def labels_for(
        self,
        group: str,
        *,
        is_admin: bool = False,
    ) -> tuple[str, ...]:
        return tuple(
            item.display_label
            for item in self.visible_items(
                group,
                is_admin=is_admin,
            )
        )

    def page_from_label(
        self,
        label: str | None,
    ) -> str:
        for item in self.items:
            if item.display_label == label:
                return item.page

        return "Home"
