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
    authenticated,
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


has_local_session = authenticated()

st.set_page_config(
    page_title="TFT Insight",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state=(
        "expanded"
        if has_local_session
        else "collapsed"
    ),
)


st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNavItems"] {
        display: none !important;
    }

    body.tft-auth-pending [data-testid="stSidebar"],
    body.tft-auth-pending [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }

    html,
    body,
    [data-testid="stAppViewContainer"],
    [data-testid="stApp"] {
        background: #0E1117 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


if auth_enabled() and not has_local_session:
    st.markdown(
        """
        <script>
        try {
            window.parent.document.body.classList.add(
                "tft-auth-pending"
            );
        } catch (e) {}
        </script>
        """,
        unsafe_allow_html=True,
    )


apply_theme()


if auth_enabled() and not require_auth():
    render_auth_page()
    st.stop()


if auth_enabled():
    st.markdown(
        """
        <script>
        try {
            window.parent.document.body.classList.remove(
                "tft-auth-pending"
            );
        } catch (e) {}
        </script>
        """,
        unsafe_allow_html=True,
    )


context = PlatformContext.from_sidebar()


if auth_enabled():
    with st.sidebar:
        user = current_user() or {}

        display_name = str(
            user.get("display_name", "")
        ).strip()

        email = str(
            user.get("email", "")
        ).strip()

        if display_name:
            st.caption(
                f"Conectado como **{display_name}**"
            )

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


with st.sidebar:
    st.markdown("#### Sistema")

    try:
        api_client.health()

        st.success("● API online")
        st.caption(
            "TFT Insight conectado ao backend."
        )

    except Exception:
        st.error("● API offline")
        st.caption(
            "Inicie a API para analisar jogadores."
        )


analytics = DashboardAnalyticsService()


PlatformRouter(
    context=context,
    api_client=api_client,
    analytics=analytics,
).render()
