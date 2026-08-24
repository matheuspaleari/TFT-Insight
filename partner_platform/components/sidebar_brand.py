from partner_platform.ui import render_html


def sidebar_brand(
    *,
    version: str = "",
) -> None:
    # P1.4 — identidade de produto; versão técnica fica fora da navegação.
    render_html(
        """
        <div class="tft-sidebar-brand">
            <div class="tft-sidebar-mark">◈</div>
            <div class="tft-sidebar-title">TFT Insight</div>
            <div class="tft-sidebar-caption">Seu coach de Teamfight Tactics</div>
        </div>
        """,
        sidebar=True,
    )
