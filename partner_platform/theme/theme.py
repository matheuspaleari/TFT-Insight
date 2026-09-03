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


DIALOG_DARK_CSS = """
/* -------------------------------------------------------------------------
   Streamlit dialog guard
   -------------------------------------------------------------------------
   Em produção, o st.dialog pode receber a superfície clara do tema nativo.
   O DOM real observado usa:
       <div data-testid="stDialog">
           <div ...>...</div>
       </div>
   Por isso, o primeiro filho de stDialog é estilizado diretamente aqui,
   no tema global carregado antes da navegação da aplicação.
------------------------------------------------------------------------- */
[data-testid="stDialog"] > div {
    background: #0f131a !important;
    background-color: #0f131a !important;
    color: #f8fafc !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    box-shadow: 0 18px 50px rgba(0, 0, 0, 0.45) !important;
}

[data-testid="stDialog"] > div > div {
    background: #0f131a !important;
    background-color: #0f131a !important;
}

[data-testid="stDialog"] h1,
[data-testid="stDialog"] h2,
[data-testid="stDialog"] h3,
[data-testid="stDialog"] h4,
[data-testid="stDialog"] p,
[data-testid="stDialog"] label,
[data-testid="stDialog"] [data-testid="stMetricLabel"],
[data-testid="stDialog"] [data-testid="stMetricValue"] {
    color: #f8fafc !important;
}

[data-testid="stDialog"] [data-testid="stCaptionContainer"],
[data-testid="stDialog"] [data-testid="stCaptionContainer"] p {
    color: #94a3b8 !important;
}

[data-testid="stDialog"] button,
[data-testid="stDialog"] button svg {
    color: #f8fafc !important;
    fill: currentColor !important;
}

[data-testid="stDialog"] [data-testid="stAlert"] {
    background: #17324b !important;
    background-color: #17324b !important;
    border-color: rgba(96, 165, 250, 0.20) !important;
}

[data-testid="stDialog"] [data-testid="stAlert"] p {
    color: #60a5fa !important;
}
"""

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

    chunks.append(DIALOG_DARK_CSS)

    st.markdown(
        "<style>"
        + "\n".join(chunks)
        + "</style>",
        unsafe_allow_html=True,
    )
