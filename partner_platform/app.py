from pathlib import Path
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

# P1.1 — esconde a navegação automática gerada pela pasta pages/ do Streamlit.
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

api_client = DashboardApiClient(
    base_url=context.api_base_url,
    api_key=context.api_key,
)

# P1.1 — status técnico deixa de ocupar uma Overview inteira e passa a ficar
# discretamente na lateral.
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
