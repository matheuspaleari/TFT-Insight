from partner_platform.components import empty_state
from partner_platform.platform_core import PlatformPage


def render(*, context) -> None:
    page = PlatformPage(
        title="Inspeção de previsão",
        subtitle="Base preparada para Feature Importance e Calibration.",
        environment=context.environment,
    )
    page.begin()

    empty_state(
        title="Módulo de previsão pronto",
        description=(
            "A próxima release conectará o inspector aos dados "
            "reais de previsão e calibração."
        ),
    )

    page.end()
