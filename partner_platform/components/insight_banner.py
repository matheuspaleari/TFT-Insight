import html

from partner_platform.ui import render_html


def insight_banner(
    *,
    eyebrow: str,
    title: str,
    description: str,
    tone: str = "neutral",
) -> None:
    tone_class = {
        "positive": "tft-insight-positive",
        "warning": "tft-insight-warning",
        "negative": "tft-insight-negative",
        "neutral": "tft-insight-neutral",
    }.get(
        tone,
        "tft-insight-neutral",
    )

    render_html(
        f"""
        <article class="tft-insight-banner {tone_class}">
            <div class="tft-insight-eyebrow">
                {html.escape(eyebrow)}
            </div>
            <div class="tft-insight-title">
                {html.escape(title)}
            </div>
            <div class="tft-insight-description">
                {html.escape(description)}
            </div>
        </article>
        """
    )
