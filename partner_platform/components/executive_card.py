import html

from partner_platform.ui import render_html


def executive_card(
    *,
    title: str,
    value: str,
    caption: str = "",
    icon: str = "◆",
    trend: str | None = None,
    trend_direction: str = "neutral",
) -> None:
    trend_class = {
        "up": "tft-trend-up",
        "down": "tft-trend-down",
        "neutral": "tft-trend-neutral",
    }.get(
        trend_direction,
        "tft-trend-neutral",
    )

    trend_html = (
        f'<span class="tft-trend {trend_class}">{html.escape(trend)}</span>'
        if trend
        else ""
    )

    render_html(
        f"""
        <article class="tft-card">
            <div class="tft-card-header">
                <div class="tft-metric-label">
                    {html.escape(title)}
                </div>
                <div class="tft-card-icon">
                    {html.escape(icon)}
                </div>
            </div>

            <div class="tft-metric-value">
                {html.escape(value)}
            </div>

            <div class="tft-metric-foot">
                <div class="tft-metric-caption">
                    {html.escape(caption)}
                </div>
                {trend_html}
            </div>
        </article>
        """
    )
