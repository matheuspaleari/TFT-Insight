from dataclasses import dataclass

from partner_platform.components import (
    compact_health_ribbon,
    render_footer,
    smart_header,
)


@dataclass(slots=True)
class PlatformPage:
    title: str
    subtitle: str
    environment: str = "Development"
    platform_version: str = "v0.6.0-alpha.2"
    hero_badges: tuple[str, ...] = (
        "Strategic Intelligence",
        "API First",
        "Explainable",
    )

    def begin(
        self,
        *,
        platform_online: bool = True,
    ) -> None:
        smart_header(
            title=self.title,
            subtitle=self.subtitle,
            environment=self.environment,
            platform_version=self.platform_version,
            badges=self.hero_badges,
        )

        compact_health_ribbon(
            [
                (
                    "API",
                    "Online"
                    if platform_online
                    else "Offline",
                    "online"
                    if platform_online
                    else "offline",
                ),
                (
                    "Engine",
                    "Healthy",
                    "online",
                ),
                (
                    "Learning",
                    "Ready",
                    "online",
                ),
                (
                    "SDK",
                    "v0.1",
                    "online",
                ),
            ]
        )

    def end(
        self,
    ) -> None:
        render_footer(
            platform_version=self.platform_version
        )
