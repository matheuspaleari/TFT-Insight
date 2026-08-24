import pandas as pd
import streamlit as st

from partner_platform.components import executive_card
from partner_platform.platform_core import PlatformPage


def render(*, context, analytics) -> None:
    page = PlatformPage(
        title="Analytics",
        subtitle="Auditoria do uso da TFT Insight API.",
        environment=context.environment,
    )
    page.begin()

    summary = analytics.summary(hours=24)

    columns = st.columns(3)

    with columns[0]:
        executive_card(
            title="Requests",
            value=str(summary["total_calls"]),
            caption="Last 24 hours",
        )

    with columns[1]:
        executive_card(
            title="Taxa de sucesso",
            value=f"{summary['success_rate']:.1f}%",
            caption="Sucesso HTTP",
        )

    with columns[2]:
        executive_card(
            title="P95",
            value=f"{summary['p95_latency_ms']:.0f} ms",
            caption="API latency",
        )

    events = analytics.recent_events(limit=100)

    if events:
        st.dataframe(
            pd.DataFrame(events),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhum evento registrado.")

    page.end()
