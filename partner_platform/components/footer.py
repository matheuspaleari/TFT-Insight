import html

from partner_platform.ui import render_html


def render_footer(
    *,
    platform_version: str = "v0.5.0-beta.1",
) -> None:
    render_html(
        f"""
        <footer class="tft-footer">
            <span>
                ◈ TFT Insight · Strategic Intelligence for Teamfight Tactics
            </span>
            <span>
                Partner Platform {html.escape(platform_version)}
                · API v1 · Contract v1
            </span>
        </footer>
        """
    )
