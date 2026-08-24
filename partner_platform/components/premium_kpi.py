from __future__ import annotations

from typing import Any

import streamlit as st

from partner_platform.ui import render_html


def premium_kpi(
    *,
    title: str,
    value: str,
    caption: str,
    icon: str,
    explanation_title: str,
    explanation_body: str,
    factors: list[dict[str, Any]] | None = None,
    technical_note: str | None = None,
    trend: str | None = None,
    trend_direction: str = "neutral",
) -> None:
    trend_class = {
        "up": "tft-kpi-trend-up",
        "down": "tft-kpi-trend-down",
        "neutral": "tft-kpi-trend-neutral",
    }.get(
        trend_direction,
        "tft-kpi-trend-neutral",
    )

    trend_html = (
        f"""
        <div class="tft-kpi-trend {trend_class}">
            {trend}
        </div>
        """
        if trend
        else """
        <div class="tft-kpi-trend tft-kpi-trend-placeholder">
            Histórico em preparação
        </div>
        """
    )

    render_html(
        f"""
        <article class="tft-premium-kpi">
            <div class="tft-premium-kpi-top">
                <div class="tft-premium-kpi-label">
                    {title}
                </div>
                <div class="tft-premium-kpi-icon">
                    {icon}
                </div>
            </div>

            <div class="tft-premium-kpi-value">
                {value}
            </div>

            <div class="tft-premium-kpi-caption">
                {caption}
            </div>

            {trend_html}
        </article>
        """
    )

    with st.popover(
        "ⓘ Entender nota",
        use_container_width=True,
    ):
        st.markdown(
            f"### {explanation_title}"
        )
        st.metric(
            label=title,
            value=value,
        )
        st.write(
            explanation_body
        )

        if factors:
            st.divider()
            st.markdown(
                "**Principais fatores**"
            )

            for item in factors:
                tone = item.get(
                    "tone",
                    "neutral",
                )

                symbol = {
                    "positive": "▲",
                    "negative": "▼",
                    "warning": "⚠",
                    "neutral": "•",
                }.get(
                    tone,
                    "•",
                )

                st.markdown(
                    f"{symbol} **{item.get('label', 'Sinal')}**"
                )
                st.caption(
                    str(
                        item.get(
                            "value",
                            "—",
                        )
                    )
                )

        if technical_note:
            st.divider()
            st.caption(
                technical_note
            )
