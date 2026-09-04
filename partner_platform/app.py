from pathlib import Path
import hmac
import os
import sys

from dotenv import load_dotenv
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from partner_platform.platform_core import (
    PlatformContext,
    PlatformRouter,
)
from partner_platform.services import (
    DashboardAnalyticsService,
    DashboardApiClient,
)
from partner_platform.theme import apply_theme


st.set_page_config(
    page_title="TFT Insight",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()


def _demo_auth_enabled() -> bool:
    return bool(
        os.getenv("TFT_INSIGHT_DEMO_USER", "").strip()
        and os.getenv("TFT_INSIGHT_DEMO_PASSWORD", "").strip()
    )


def _authenticated() -> bool:
    return bool(st.session_state.get("tft_demo_authenticated", False))


def _check_credentials(username: str, password: str) -> bool:
    expected_user = os.getenv("TFT_INSIGHT_DEMO_USER", "").strip()
    expected_password = os.getenv("TFT_INSIGHT_DEMO_PASSWORD", "").strip()

    return (
        hmac.compare_digest(username.strip(), expected_user)
        and hmac.compare_digest(password, expected_password)
    )


def _render_login() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNavItems"] {
            display: none !important;
        }

        .block-container {
            max-width: 620px;
            padding-top: 8vh;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## TFT Insight")
    st.caption("Acesso privado de demonstração")

    with st.container(border=True):
        st.markdown("### Entrar")
        st.write(
            "Esta versão está disponível apenas para participantes "
            "autorizados do teste."
        )

        with st.form("tft_demo_login", clear_on_submit=False):
            username = st.text_input(
                "Usuário",
                autocomplete="username",
            )
            password = st.text_input(
                "Senha",
                type="password",
                autocomplete="current-password",
            )

            submitted = st.form_submit_button(
                "Acessar TFT Insight",
                width="stretch",
            )

        if submitted:
            if _check_credentials(username, password):
                st.session_state["tft_demo_authenticated"] = True
                st.session_state["tft_demo_user"] = username.strip()
                st.rerun()

            st.error("Usuário ou senha inválidos.")

    st.caption(
        "Demo privada. O acesso pode ser removido ou alterado a qualquer momento."
    )


def _render_logout() -> None:
    with st.sidebar:
        demo_user = str(
            st.session_state.get("tft_demo_user", "")
        ).strip()

        if demo_user:
            st.caption(f"Demo: {demo_user}")

        if st.button(
            "Sair da demo",
            width="stretch",
            key="tft_demo_logout",
        ):
            st.session_state.pop("tft_demo_authenticated", None)
            st.session_state.pop("tft_demo_user", None)
            st.rerun()


if _demo_auth_enabled() and not _authenticated():
    _render_login()
    st.stop()


# Esconde a navegação automática gerada pela pasta pages/ do Streamlit.
# As páginas antigas continuam no projeto para desenvolvimento/compatibilidade,
# mas deixam de ser expostas ao jogador.
st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNavItems"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

context = PlatformContext.from_sidebar()

if _demo_auth_enabled():
    _render_logout()

api_client = DashboardApiClient(
    base_url=context.api_base_url,
    api_key=context.api_key,
)

# O status técnico fica discretamente na lateral.
with st.sidebar:
    st.markdown("#### Sistema")
    try:
        api_client.health()
        st.success("● API online")
        st.caption("TFT Insight conectado ao backend.")
    except Exception:
        st.error("● API offline")
        st.caption("Inicie a API para analisar jogadores.")

analytics = DashboardAnalyticsService()

PlatformRouter(
    context=context,
    api_client=api_client,
    analytics=analytics,
).render()
