import html

from partner_platform.ui import render_html


def feature_header(
    *,
    title: str,
    description: str,
    kicker: str | None = None,
) -> None:
    kicker_html = (
        f'<div class="tft-eyebrow">{html.escape(kicker)}</div>'
        if kicker
        else ""
    )

    render_html(
        f"""
        <div class="tft-feature-header">
            {kicker_html}
            <div class="tft-section-title">
                {html.escape(title)}
            </div>
            <div class="tft-section-subtitle">
                {html.escape(description)}
            </div>
        </div>
        """
    )
