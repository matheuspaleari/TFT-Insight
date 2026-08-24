import html

from partner_platform.ui import render_html


def executive_spotlight(
    *,
    eyebrow: str,
    title: str,
    value: str,
    description: str,
    tone: str = "neutral",
    symbol: str = "◆",
) -> None:
    tone_class = {
        "positive": "tft-spotlight-positive",
        "warning": "tft-spotlight-warning",
        "neutral": "tft-spotlight-neutral",
    }.get(
        tone,
        "tft-spotlight-neutral",
    )

    render_html(
        f"""
        <article class="tft-executive-spotlight {tone_class}">
            <div class="tft-executive-spotlight-symbol">
                {html.escape(symbol)}
            </div>
            <div class="tft-executive-spotlight-eyebrow">
                {html.escape(eyebrow)}
            </div>
            <div class="tft-executive-spotlight-title">
                {html.escape(title)}
            </div>
            <div class="tft-executive-spotlight-value">
                {html.escape(value)}
            </div>
            <div class="tft-executive-spotlight-description">
                {html.escape(description)}
            </div>
        </article>
        """
    )
