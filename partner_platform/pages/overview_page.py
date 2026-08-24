import pandas as pd
import plotly.express as px
import streamlit as st

from partner_platform.components import (
    chart_card,
    executive_card,
    section_header,
)
from partner_platform.platform_core import PlatformPage


def render(*, context, api_client, analytics) -> None:
    try:
        health = api_client.health()
        online = health.get("status") == "ok"
    except Exception:
        online = False

    page = PlatformPage(
        title="Strategic Intelligence for Teamfight Tactics",
        subtitle=(
            "Operate, measure and integrate the TFT Insight Engine "
            "through a single partner workspace."
        ),
        environment=context.environment,
        hero_badges=(
            "Partner Platform",
            "API v1",
            "Contract v1",
            "Explainability First",
        ),
    )
    page.begin(platform_online=online)

    summary = analytics.summary(hours=24)

    columns = st.columns(4)

    with columns[0]:
        executive_card(
            title="API Health",
            value="Online" if online else "Offline",
            caption="Current service status",
            icon="●",
            trend="Healthy" if online else "Attention",
            trend_direction="up" if online else "down",
        )

    with columns[1]:
        executive_card(
            title="Calls · 24h",
            value=f"{summary['total_calls']:,}",
            caption=f"{summary['success_rate']:.1f}% success",
            icon="↗",
            trend="Live",
            trend_direction="neutral",
        )

    with columns[2]:
        executive_card(
            title="Avg latency",
            value=f"{summary['average_latency_ms']:.0f} ms",
            caption=f"P95 {summary['p95_latency_ms']:.0f} ms",
            icon="⚡",
            trend="Observed",
            trend_direction="neutral",
        )

    with columns[3]:
        executive_card(
            title="Cache hit",
            value=f"{summary['cache_hit_rate']:.1f}%",
            caption="Avoided repeated downloads",
            icon="↻",
            trend="Efficient",
            trend_direction="up",
        )

    section_header(
        "Traffic",
        subtitle="Partner API usage over the last 14 days",
    )

    usage = analytics.daily_usage(days=14)

    if usage:
        frame = pd.DataFrame(usage)

        with chart_card(
            "API Calls",
            subtitle="Requests per day",
        ):
            chart = px.area(
                frame,
                x="day",
                y="calls",
                markers=True,
            )

            chart.update_layout(
                height=360,
                margin=dict(l=0, r=0, t=5, b=0),
                xaxis_title=None,
                yaxis_title=None,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A1B5"),
                showlegend=False,
            )
            chart.update_xaxes(
                showgrid=False,
                zeroline=False,
            )
            chart.update_yaxes(
                gridcolor="rgba(255,255,255,.045)",
                zeroline=False,
            )

            st.plotly_chart(
                chart,
                use_container_width=True,
            )
    else:
        st.info(
            "Traffic data will appear after API calls are recorded."
        )

    page.end()
