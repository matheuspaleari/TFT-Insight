from __future__ import annotations

from typing import Any

import streamlit as st

from partner_platform.components.executive_card import (
    executive_card,
)


def explainable_kpi(
    *,
    title: str,
    value: str,
    caption: str,
    icon: str,
    explanation_title: str,
    explanation_body: str,
    factors: list[dict[str, Any]] | None = None,
    technical_note: str | None = None,
) -> None:
    executive_card(
        title=title,
        value=value,
        caption=caption,
        icon=icon,
    )

    st.caption(
        "ⓘ Clique para entender"
    )

    with st.popover(
        f"Por que {title}?",
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
                label = str(
                    item.get(
                        "label",
                        "Sinal",
                    )
                )
                value_text = str(
                    item.get(
                        "value",
                        "—",
                    )
                )
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

                st.write(
                    f"{symbol} **{label}**"
                )
                st.caption(
                    value_text
                )

        if technical_note:
            st.divider()
            st.caption(
                technical_note
            )
