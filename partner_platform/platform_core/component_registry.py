from dataclasses import dataclass
from typing import Callable


@dataclass(slots=True, frozen=True)
class RegisteredComponent:
    name: str
    component: Callable
    category: str


class ComponentRegistry:
    @classmethod
    def default(
        cls,
    ) -> tuple[RegisteredComponent, ...]:
        # Lazy import mantém o registry fora da cadeia de inicialização.
        from partner_platform import components

        return (
            RegisteredComponent(
                "hero",
                components.hero,
                "layout",
            ),
            RegisteredComponent(
                "executive_card",
                components.executive_card,
                "data-display",
            ),
            RegisteredComponent(
                "health_ribbon",
                components.health_ribbon,
                "status",
            ),
            RegisteredComponent(
                "chart_card",
                components.chart_card,
                "visualization",
            ),
            RegisteredComponent(
                "loading_pipeline",
                components.loading_pipeline,
                "feedback",
            ),
            RegisteredComponent(
                "empty_state",
                components.empty_state,
                "feedback",
            ),
        )
