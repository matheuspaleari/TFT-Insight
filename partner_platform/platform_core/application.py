from collections.abc import Callable

from .context import PlatformContext
from .feature_registry import FeatureRegistry
from .layout import PlatformLayout
from .navigation import NavigationEngine
from .router import PlatformRouter


class PlatformApplication:
    """Composition root da Partner Platform."""

    def __init__(
        self,
        *,
        api_client_factory: Callable,
        analytics_factory: Callable,
    ) -> None:
        self.api_client_factory = api_client_factory
        self.analytics_factory = analytics_factory

    def run(self) -> None:
        navigation = NavigationEngine.default()

        context = PlatformContext.from_sidebar(
            navigation=navigation
        )

        api_client = self.api_client_factory(context)
        analytics = self.analytics_factory()

        registry = FeatureRegistry.default()

        layout = PlatformLayout(
            context=context,
            api_client=api_client,
        )

        PlatformRouter(
            context=context,
            registry=registry,
            api_client=api_client,
            analytics=analytics,
            layout=layout,
        ).render()
