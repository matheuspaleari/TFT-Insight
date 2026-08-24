from contextlib import contextmanager

import streamlit as st


@contextmanager
def panel():
    with st.container(border=True):
        yield
