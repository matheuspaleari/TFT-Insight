import re
from textwrap import dedent

import streamlit as st


_TAG_GAP = re.compile(r">\s+<")
_LINE_GAP = re.compile(r"\s*\n\s*")


def normalize_html(markup: str) -> str:
    """
    Normaliza HTML para uma única linha.

    Motivo:
    Streamlit usa Markdown antes de renderizar HTML. Linhas internas
    iniciadas com quatro espaços podem ser interpretadas como blocos
    de código mesmo quando `unsafe_allow_html=True`.

    Remover apenas a indentação externa com `dedent()` não é suficiente.
    Esta função também remove quebras de linha entre tags.
    """
    normalized = dedent(markup).strip()
    normalized = _TAG_GAP.sub("><", normalized)
    normalized = _LINE_GAP.sub(" ", normalized)
    return normalized.strip()


def render_html(
    markup: str,
    *,
    sidebar: bool = False,
) -> None:
    """
    Único ponto autorizado para renderização de HTML visual
    na Partner Platform.
    """
    normalized = normalize_html(markup)

    target = (
        st.sidebar.markdown
        if sidebar
        else st.markdown
    )

    target(
        normalized,
        unsafe_allow_html=True,
    )
