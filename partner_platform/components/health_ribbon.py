import html

from partner_platform.ui import render_html


def health_ribbon(
    items: list[tuple[str, str, str]],
) -> None:
    blocks = []

    for label, value, status in items:
        dot_class = {
            "online": "tft-dot-online",
            "warning": "tft-dot-warning",
            "offline": "tft-dot-offline",
        }.get(
            status,
            "tft-dot-online",
        )

        blocks.append(
            f"""
            <div class="tft-health-item">
                <div class="tft-health-label">
                    {html.escape(label)}
                </div>
                <div class="tft-health-value">
                    <span class="tft-dot {dot_class}"></span>
                    {html.escape(value)}
                </div>
            </div>
            """
        )

    render_html(
        '<div class="tft-health-ribbon">'
        + "".join(blocks)
        + "</div>"
    )
