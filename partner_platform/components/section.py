import html

from partner_platform.ui import render_html


def section_header(
    title: str,
    *,
    subtitle: str = "",
) -> None:
    render_html(
        f"""
        <div class="tft-section-header">
            <div>
                <div class="tft-section-title">
                    {html.escape(title)}
                </div>
                <div class="tft-section-subtitle">
                    {html.escape(subtitle)}
                </div>
            </div>
        </div>
        """
    )
