from contextlib import contextmanager

import streamlit as st

from .section import section_header


@contextmanager
def chart_card(
    title: str,
    *,
    subtitle: str = "",
):
    with st.container(border=True):
        section_header(
            title,
            subtitle=subtitle,
        )
        yield
