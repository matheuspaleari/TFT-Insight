from dataclasses import dataclass

from partner_platform.components import (
    health_ribbon,
    render_footer,
    topbar,
)

from .health import PlatformHealth


@dataclass(slots=True)
class PlatformLayout:
    context: object
    api_client: object

    def begin(self) -> PlatformHealth:
        health = PlatformHealth.resolve(
            self.api_client
        )

        topbar(
            environment=self.context.environment,
            platform_version=self.context.platform_version,
        )

        health_ribbon(
            [
                (
                    "API",
                    (
                        "Online"
                        if health.api_online
                        else "Offline"
                    ),
                    (
                        "online"
                        if health.api_online
                        else "offline"
                    ),
                ),
                (
                    "Engine",
                    health.engine_status,
                    "online",
                ),
                (
                    "Learning",
                    health.learning_status,
                    "online",
                ),
                (
                    "SDK",
                    health.sdk_version,
                    "online",
                ),
            ]
        )

        return health

    def end(self) -> None:
        render_footer(
            platform_version=(
                self.context.platform_version
            )
        )
