from pathlib import Path

import streamlit as st


ASSET_DIR = (
    Path(__file__).resolve().parents[1]
    / "assets"
)


CSS_FILES = (
    # Base histórica
    ASSET_DIR / "theme.css",
    ASSET_DIR / "platform_framework.css",
    ASSET_DIR / "explainability.css",
    ASSET_DIR / "ux_polish.css",
    ASSET_DIR / "product_intelligence.css",
    ASSET_DIR / "player_context.css",
    ASSET_DIR / "executive_v2.css",
    ASSET_DIR / "smart_header.css",
    ASSET_DIR / "ux_polish_v1.css",

    # Roadmap 22
    ASSET_DIR / "roadmap22.css",
    ASSET_DIR / "roadmap22_shell.css",
    ASSET_DIR / "roadmap22_intelligence.css",
    ASSET_DIR / "roadmap22_responsive.css",
    ASSET_DIR / "roadmap23_home.css",
    ASSET_DIR / "roadmap23_intelligence.css",
    ASSET_DIR / "roadmap23_coach.css",
    ASSET_DIR / "roadmap23_trust.css",
    ASSET_DIR / "roadmap23_finish.css",
)


def apply_theme() -> None:
    """
    Carrega o tema visual da Partner Platform.

    Roadmap 22:
    - mantém as folhas históricas por compatibilidade;
    - consolida acabamento em roadmap22.css;
    - aplica shell/hierarquia por último em roadmap22_shell.css.
    """

    chunks: list[str] = []

    for path in CSS_FILES:
        if not path.exists():
            continue

        chunks.append(
            path.read_text(
                encoding="utf-8"
            )
        )

    if not chunks:
        return

    st.markdown(
        "<style>"
        + "\n".join(chunks)
        + "</style>",
        unsafe_allow_html=True,
    )
