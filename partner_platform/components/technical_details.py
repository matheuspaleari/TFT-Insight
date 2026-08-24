import json
from typing import Any

import streamlit as st


def technical_details(
    payload: Any,
    *,
    title: str = "Detalhes técnicos",
    language: str = "json",
) -> None:
    with st.expander(
        f"▸ {title}",
        expanded=False,
    ):
        if language == "json":
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    st.code(payload)
                    return

            st.json(payload)
            return

        st.code(
            str(payload),
            language=language,
        )
