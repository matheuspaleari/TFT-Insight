import html

from partner_platform.ui import render_html


def loading_screen(
    *,
    title: str = "Analisando jogador",
    message: str = "Preparando a inteligência da partida.",
    steps: tuple[str, ...] = (
        "Riot API",
        "Cache",
        "Transformers",
        "Decision",
        "Learning",
        "Previsão",
    ),
) -> None:
    steps_html = "".join(
        (
            '<div class="tft-loading-step">'
            '<span class="tft-loading-dot"></span>'
            f"<span>{html.escape(step)}</span>"
            "</div>"
        )
        for step in steps
    )

    render_html(
        f"""
        <div class="tft-loading-shell">
            <div class="tft-loading-orb">◈</div>
            <div class="tft-loading-title">
                {html.escape(title)}
            </div>
            <div class="tft-loading-message">
                {html.escape(message)}
            </div>
            <div class="tft-loading-progress">
                <div class="tft-loading-progress-fill"></div>
            </div>
            <div class="tft-loading-steps">
                {steps_html}
            </div>
        </div>
        """
    )
