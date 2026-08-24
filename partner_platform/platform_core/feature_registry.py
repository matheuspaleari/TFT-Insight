from dataclasses import dataclass
from typing import Callable


@dataclass(slots=True, frozen=True)
class FeatureModule:
    key: str
    render: Callable


class FeatureRegistry:
    def __init__(
        self,
        modules: tuple[FeatureModule, ...],
    ) -> None:
        self._modules = {
            module.key: module
            for module in modules
        }

    @classmethod
    def default(cls) -> "FeatureRegistry":
        # Lazy import: evita ciclo platform_core -> pages -> platform_core
        from partner_platform.pages import (
            analytics_page,
            benchmark_page,
            developer_page,
            overview_page,
            playground_page,
            prediction_page,
            settings_page,
        )

        return cls(
            modules=(
                FeatureModule("overview", overview_page.render),
                FeatureModule("playground", playground_page.render),
                FeatureModule("benchmark", benchmark_page.render),
                FeatureModule("prediction", prediction_page.render),
                FeatureModule("analytics", analytics_page.render),
                FeatureModule("developer", developer_page.render),
                FeatureModule("settings", settings_page.render),
            )
        )

    def get(
        self,
        key: str,
    ) -> FeatureModule | None:
        return self._modules.get(key)

    def keys(self) -> tuple[str, ...]:
        return tuple(self._modules)
