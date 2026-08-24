import html

from partner_platform.ui import render_html


def summary_row(
    *,
    label: str,
    value: str,
    description: str = "",
) -> None:
    render_html(
        f"""
        <div class="tft-summary-row">
            <div>
                <div class="tft-summary-label">
                    {html.escape(label)}
                </div>
                <div class="tft-summary-description">
                    {html.escape(description)}
                </div>
            </div>
            <div class="tft-summary-value">
                {html.escape(value)}
            </div>
        </div>
        """
    )
