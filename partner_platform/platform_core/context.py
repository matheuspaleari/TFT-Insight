from dataclasses import dataclass
import os

import streamlit as st

from partner_platform.components import (
    current_session_panel,
    sidebar_brand,
)
from partner_platform.navigation import NavigationCatalog


@dataclass(slots=True, frozen=True)
class PlatformContext:
    page: str
    api_base_url: str
    api_key: str | None
    environment: str = "Development"
    platform_version: str = "v0.6.0-alpha.2"

    @classmethod
    def from_sidebar(cls):
        sidebar_brand()
        current_session_panel()

        catalog = NavigationCatalog.default()

        pending_page = st.session_state.pop(
            "_tft_navigation_target",
            None,
        )

        if pending_page:
            pending_label = next(
                (
                    item.display_label
                    for item in catalog.items
                    if item.page == pending_page
                ),
                None,
            )

            if pending_label is not None:
                st.session_state[
                    "tft_product_navigation"
                ] = pending_label

        st.sidebar.markdown("#### Navegação")
        choice = st.sidebar.radio(
            "Navegação TFT Insight",
            options=catalog.labels_for("Principal"),
            label_visibility="collapsed",
            key="tft_product_navigation",
        )

        page = catalog.page_from_label(choice)

        configured_api_url = os.getenv(
            "TFT_INSIGHT_API_BASE_URL",
            "http://127.0.0.1:8000",
        ).strip().rstrip("/")

        configured_api_key = os.getenv(
            "TFT_INSIGHT_API_KEY",
            "",
        ).strip() or None

        configured_environment = os.getenv(
            "TFT_INSIGHT_ENVIRONMENT",
            "Development",
        ).strip()

        # Em produção, configuração técnica vem exclusivamente do ambiente.
        # Em desenvolvimento/staging, mantemos os controles para facilitar testes.
        if configured_environment.lower() == "production":
            api_base_url = configured_api_url
            api_key = configured_api_key
            environment = "Production"
        else:
            with st.sidebar.expander(
                "Configuração técnica",
                expanded=False,
            ):
                api_base_url = st.text_input(
                    "API Base URL",
                    value=configured_api_url,
                )
                api_key = st.text_input(
                    "API Key",
                    value=configured_api_key or "",
                    type="password",
                )
                environment = st.selectbox(
                    "Ambiente",
                    options=["Development", "Staging", "Production"],
                    index=(
                        1
                        if configured_environment.lower() == "staging"
                        else 0
                    ),
                )

        return cls(
            page=page,
            api_base_url=api_base_url.strip().rstrip("/"),
            api_key=api_key.strip() if isinstance(api_key, str) else api_key,
            environment=environment,
        )
