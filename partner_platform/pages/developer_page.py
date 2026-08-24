import streamlit as st

from partner_platform.platform_core import PlatformPage


def render(*, context) -> None:
    page = PlatformPage(
        title="Desenvolvimento",
        subtitle="Quick Start para API e Python SDK.",
        environment=context.environment,
    )
    page.begin()

    st.code(
        """
from tft_insight import TFTInsightClient

with TFTInsightClient(
    base_url="http://127.0.0.1:8000"
) as client:
    report = client.analyze_player(
        game_name="Pinador doss",
        tag_line="000"
    )
""".strip(),
        language="python",
    )

    st.code(
        """
POST /v1/analyze/player
Content-Type: application/json
""".strip(),
        language="http",
    )

    page.end()
