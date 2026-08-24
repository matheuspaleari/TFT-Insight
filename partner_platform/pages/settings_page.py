import streamlit as st

from partner_platform.platform_core import PlatformPage


def render(*, context) -> None:
    page = PlatformPage(
        title="Configurações",
        subtitle="Configurações locais da Partner Platform.",
        environment=context.environment,
    )
    page.begin()

    st.text_input(
        "Environment",
        value=context.environment,
        disabled=True,
    )

    st.text_input(
        "API Base URL",
        value=context.api_base_url,
        disabled=True,
    )

    page.end()
