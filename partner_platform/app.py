from pathlib import Path
import sys

from dotenv import load_dotenv
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from partner_platform.auth.login_page import render_auth_page
from partner_platform.auth.session import (
    auth_enabled,
    clear_session,
    current_user,
    require_auth,
)
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


if auth_enabled() and not require_auth():
    render_auth_page()
    st.stop()


# Esconde a navegação automática gerada pela pasta pages/ do Streamlit.
# As páginas antigas continuam no projeto para desenvolvimento/compatibilidade,
# mas deixam de ser expostas ao jogador.
st.markdown(
    '''
    <style>
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNavItems"] {
        display: none !important;
    }
    </style>
    ''',
    unsafe_allow_html=True,
)


context = PlatformContext.from_sidebar()


if auth_enabled():
    with st.sidebar:
        user = current_user() or {}
        display_name = str(user.get("display_name", "")).strip()
        email = str(user.get("email", "")).strip()

        if display_name:
            st.caption(f"Conectado como **{display_name}**")
        if email:
            st.caption(email)

        if st.button(
            "Sair",
            width="stretch",
            key="tft_auth_logout",
        ):
            clear_session()
            st.rerun()


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
