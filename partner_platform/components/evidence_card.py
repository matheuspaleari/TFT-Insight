import html

from partner_platform.ui import render_html


def evidence_card(
    *,
    title: str,
    value: str,
    description: str,
    status: str = "neutral",
) -> None:
    status_class = {
        "positive": "tft-evidence-positive",
        "warning": "tft-evidence-warning",
        "negative": "tft-evidence-negative",
        "neutral": "tft-evidence-neutral",
    }.get(
        status,
        "tft-evidence-neutral",
    )

    render_html(
        f"""
        <article class="tft-evidence-card {status_class}">
            <div class="tft-evidence-title">
                {html.escape(title)}
            </div>
            <div class="tft-evidence-value">
                {html.escape(value)}
            </div>
            <div class="tft-evidence-description">
                {html.escape(description)}
            </div>
        </article>
        """
    )
