from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class NavigationItem:
    key: str
    label: str
    icon: str
    group: str
    description: str = ""


class NavigationEngine:
    def __init__(
        self,
        items: tuple[NavigationItem, ...],
    ) -> None:
        self.items = items

    @classmethod
    def default(cls) -> "NavigationEngine":
        return cls(
            items=(
                NavigationItem(
                    key="overview",
                    label="Overview",
                    icon="◫",
                    group="Platform",
                    description="Executive operations",
                ),
                NavigationItem(
                    key="playground",
                    label="Playground",
                    icon="⚡",
                    group="Platform",
                    description="Run player analysis",
                ),
                NavigationItem(
                    key="benchmark",
                    label="Benchmark",
                    icon="⌁",
                    group="Intelligence",
                    description="Challenger intelligence",
                ),
                NavigationItem(
                    key="prediction",
                    label="Prediction",
                    icon="◆",
                    group="Intelligence",
                    description="Prediction inspector",
                ),
                NavigationItem(
                    key="analytics",
                    label="Analytics",
                    icon="◌",
                    group="Intelligence",
                    description="Partner usage analytics",
                ),
                NavigationItem(
                    key="developer",
                    label="Developer",
                    icon="</>",
                    group="Workspace",
                    description="Developer experience",
                ),
                NavigationItem(
                    key="settings",
                    label="Settings",
                    icon="⚙",
                    group="Workspace",
                    description="Platform configuration",
                ),
            )
        )

    def groups(self) -> tuple[str, ...]:
        seen = []

        for item in self.items:
            if item.group not in seen:
                seen.append(item.group)

        return tuple(seen)

    def items_for_group(
        self,
        group: str,
    ) -> tuple[NavigationItem, ...]:
        return tuple(
            item
            for item in self.items
            if item.group == group
        )

    def get(
        self,
        key: str,
    ) -> NavigationItem | None:
        return next(
            (
                item
                for item in self.items
                if item.key == key
            ),
            None,
        )
