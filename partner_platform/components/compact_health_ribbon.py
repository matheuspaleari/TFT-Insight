import html

from partner_platform.ui import render_html


def compact_health_ribbon(
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
            <div class="tft-compact-health-item">
                <span class="tft-dot {dot_class}"></span>
                <span class="tft-compact-health-label">
                    {html.escape(label)}
                </span>
                <span class="tft-compact-health-value">
                    {html.escape(value)}
                </span>
            </div>
            """
        )

    render_html(
        '<div class="tft-compact-health">'
        + "".join(blocks)
        + "</div>"
    )
