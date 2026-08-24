import html

from partner_platform.ui import render_html


def smart_header(
    *,
    title: str,
    subtitle: str,
    environment: str,
    platform_version: str,
    badges: tuple[str, ...] = (),
) -> None:
    badges_html = "".join(
        f'<span class="tft-smart-header-chip">{html.escape(item)}</span>'
        for item in badges
    )

    render_html(
        f"""
        <header class="tft-smart-header">
            <div class="tft-smart-header-top">
                <div class="tft-smart-header-brand">
                    <span class="tft-smart-header-mark">◈</span>
                    <span class="tft-smart-header-brand-name">TFT Insight</span>
                    <span class="tft-smart-header-version">
                        {html.escape(platform_version)}
                    </span>
                </div>

                <div class="tft-smart-header-env">
                    <span class="tft-smart-header-dot"></span>
                    {html.escape(environment)}
                </div>
            </div>

            <div class="tft-smart-header-body">
                <div>
                    <div class="tft-smart-header-title">
                        {html.escape(title)}
                    </div>
                    <div class="tft-smart-header-subtitle">
                        {html.escape(subtitle)}
                    </div>
                </div>

                <div class="tft-smart-header-badges">
                    {badges_html}
                </div>
            </div>
        </header>
        """
    )
